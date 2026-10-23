"""Passe d'évaluation de l'assistant : envoie chaque question de référence au modèle et produit
un tableau CSV que des locuteurs notent ensuite (voir evaluation/chat/README.md).

    uv run python -m app.evaluation.chat_eval QUESTIONS.jsonl DOSSIER_RESULTATS

Chaque question est posée dans une conversation neuve. Le script ne note rien lui-même : il ne
prétend pas juger la qualité du tamasheq.
"""

import argparse
import asyncio
import csv
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.ai.chat import ChatMessage, ChatProvider, ChatProviderError
from app.ai.prompts import CHAT_SYSTEM_PROMPT

REQUIRED = ("id", "category", "language", "question")

# Colonnes laissées vides, remplies par chaque évaluateur (barème : evaluation/chat/README.md).
RATING_COLUMNS = (
    "evaluateur",
    "sens_0_2",
    "langue_0_2",
    "orthographe_0_2",
    "mots_inventes_oui_non",
    "incertitude_signalee_oui_non",
    "refus_injustifie_oui_non",
    "commentaire",
)


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    language: str
    question: str
    variant: str
    reference: str


def load_questions(path: Path) -> list[Question]:
    questions: list[Question] = []
    seen: set[str] = set()
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        missing = [k for k in REQUIRED if not str(item.get(k, "")).strip()]
        if missing:
            raise ValueError(f"ligne {n} : champs manquants {missing}")
        if item["id"] in seen:
            raise ValueError(f"ligne {n} : identifiant en double {item['id']!r}")
        seen.add(item["id"])
        questions.append(
            Question(
                id=item["id"],
                category=item["category"],
                language=item["language"],
                question=item["question"],
                variant=item.get("variant", ""),
                reference=item.get("reference", ""),
            )
        )
    return questions


async def run(questions: list[Question], provider: ChatProvider) -> list[dict[str, str]]:
    prompt_hash = hashlib.sha256(CHAT_SYSTEM_PROMPT.encode()).hexdigest()[:12]
    rows: list[dict[str, str]] = []
    for q in questions:
        row = {
            "id": q.id,
            "category": q.category,
            "language": q.language,
            "variant": q.variant,
            "question": q.question,
            "reference": q.reference,
            "provider": provider.name,
            "date_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "prompt_sha256": prompt_hash,
        }
        try:
            reply = await provider.reply([ChatMessage("user", q.question)])
            row |= {"model": reply.model, "reply": reply.text, "error": ""}
            if reply.truncated:
                row["error"] = "truncated"
        except ChatProviderError as e:
            row |= {"model": "", "reply": "", "error": e.kind}
        rows.append(row | dict.fromkeys(RATING_COLUMNS, ""))
    return rows


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("questions", type=Path)
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args()

    from app.routers.chat import get_chat_provider

    provider = get_chat_provider()
    if provider is None:
        sys.exit("ANTHROPIC_API_KEY absente : rien n'est envoyé.")
    questions = load_questions(args.questions)
    rows = asyncio.run(run(questions, provider))
    model = next((r["model"] for r in rows if r["model"]), "inconnu")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = args.out_dir / f"{stamp}_{model}.csv"
    write_csv(rows, out)
    errors = sum(1 for r in rows if r["error"])
    print(f"{len(rows)} questions, {errors} erreurs → {out}")


if __name__ == "__main__":
    main()
