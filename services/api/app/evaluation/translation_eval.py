"""Passe d'évaluation de la traduction (voir evaluation/translation/README.md).

    uv run python -m app.evaluation.translation_eval PHRASES.jsonl DOSSIER [--no-glossary]

Les références doivent être écrites par des locuteurs et ne jamais servir à l'entraînement ni
à l'ajustement des consignes. chrF++ est calculé quand une référence existe ; c'est un
indicateur, pas une preuve de qualité : la notation humaine reste nécessaire.
"""

import argparse
import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.ai.chat import ChatProviderError
from app.ai.prompts import TRANSLATION_SYSTEM_PROMPT
from app.ai.translation import Lang, TranslationProvider
from app.evaluation.chat_eval import write_csv
from app.services import glossary

RATING_COLUMNS = (
    "evaluateur",
    "fidelite_0_2",
    "grammaire_0_2",
    "naturel_0_2",
    "orthographe_0_2",
    "omissions_oui_non",
    "ajouts_oui_non",
    "hallucinations_oui_non",
    "commentaire",
)


@dataclass(frozen=True)
class Sentence:
    id: str
    source_lang: Lang
    target_lang: Lang
    text: str
    reference: str
    variant: str


def load(path: Path) -> list[Sentence]:
    items: list[Sentence] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        d = json.loads(line)
        if {d.get("source_lang"), d.get("target_lang")} not in ({"taq", "fr"}, {"taq", "en"}):
            raise ValueError(f"ligne {n} : direction invalide")
        if not str(d.get("id", "")).strip() or not str(d.get("text", "")).strip():
            raise ValueError(f"ligne {n} : id et text obligatoires")
        items.append(
            Sentence(
                d["id"],
                d["source_lang"],
                d["target_lang"],
                d["text"],
                d.get("reference", ""),
                d.get("variant", ""),
            )
        )
    return items


def chrf(hypothesis: str, reference: str) -> float:
    from sacrebleu.metrics.chrf import CHRF

    return float(CHRF(word_order=2).sentence_score(hypothesis, [reference]).score)


def corpus_chrf(hypotheses: list[str], references: list[str]) -> float:
    from sacrebleu.metrics.chrf import CHRF

    return float(CHRF(word_order=2).corpus_score(hypotheses, [references]).score)


async def run(
    sentences: list[Sentence],
    provider: TranslationProvider,
    session: Session | None,
) -> list[dict[str, str]]:
    prompt_hash = hashlib.sha256(TRANSLATION_SYSTEM_PROMPT.encode()).hexdigest()[:12]
    rows: list[dict[str, str]] = []
    for s in sentences:
        entries = glossary.lookup(session, s.text, s.source_lang) if session else []
        row = {
            "id": s.id,
            "direction": f"{s.source_lang}->{s.target_lang}",
            "variant": s.variant,
            "text": s.text,
            "reference": s.reference,
            "glossary": "oui" if session else "non",
            "date_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "prompt_sha256": prompt_hash,
        }
        try:
            t = await provider.translate(
                s.text, s.source_lang, s.target_lang, s.variant or None, entries
            )
            row |= {
                "model": t.model,
                "translation": t.translation,
                "alternatives": " | ".join(t.alternatives),
                "notes": t.notes,
                "glossary_used": " ".join(t.glossary_used),
                "chrf_pp": f"{chrf(t.translation, s.reference):.1f}" if s.reference else "",
                "error": "truncated" if t.truncated else "",
            }
        except ChatProviderError as e:
            row |= {
                "model": "",
                "translation": "",
                "alternatives": "",
                "notes": "",
                "glossary_used": "",
                "chrf_pp": "",
                "error": e.kind,
            }
        rows.append(row | dict.fromkeys(RATING_COLUMNS, ""))
    return rows


def summary(rows: list[dict[str, str]]) -> str:
    lines = []
    for direction in sorted({r["direction"] for r in rows}):
        scored = [r for r in rows if r["direction"] == direction and r["reference"] and r["model"]]
        if scored:
            score = corpus_chrf(
                [r["translation"] for r in scored], [r["reference"] for r in scored]
            )
            lines.append(f"{direction} : chrF++ {score:.1f} sur {len(scored)} phrases")
        else:
            lines.append(f"{direction} : aucune référence, pas de score automatique")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sentences", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--no-glossary", action="store_true", help="sans le dictionnaire validé")
    args = parser.parse_args()

    from app.db import get_engine
    from app.routers.translate import get_translation_provider

    provider = get_translation_provider()
    if provider is None:
        sys.exit("ANTHROPIC_API_KEY absente : rien n'est envoyé.")
    sentences = load(args.sentences)
    with Session(get_engine()) as session:
        rows = asyncio.run(run(sentences, provider, None if args.no_glossary else session))
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    model = next((r["model"] for r in rows if r["model"]), "inconnu")
    out = args.out_dir / f"{stamp}_{model}{'_sans-glossaire' if args.no_glossary else ''}.csv"
    write_csv(rows, out)
    print(summary(rows))
    print(f"→ {out}")


if __name__ == "__main__":
    main()
