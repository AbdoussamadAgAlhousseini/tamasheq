"""Évaluation de la reconnaissance vocale : WER et CER (voir evaluation/voice/README.md).

    uv run python -m app.evaluation.asr_eval RESULTATS.jsonl

Indépendant du modèle : le fichier contient, pour chaque enregistrement de test, la
transcription de référence (validée par un locuteur) et l'hypothèse produite par le système
évalué, exécuté ailleurs si besoin (GPU). Une ligne :

    {"id": "…", "reference": "…", "hypothesis": "…", "speaker": "…", "condition": "…"}

Normalisation appliquée avant comparaison, identique pour la référence et l'hypothèse :
NFC, minuscules, suppression de la ponctuation Unicode (catégories P*), espaces réduits.
Les diacritiques sont conservés : ḍ et d restent des lettres différentes.
"""

import argparse
import json
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold()
    text = "".join(" " if unicodedata.category(c).startswith("P") else c for c in text)
    return " ".join(text.split())


def edit_distance[T](reference: list[T], hypothesis: list[T]) -> int:
    """Distance de Levenshtein (substitutions, insertions, suppressions)."""
    previous = list(range(len(hypothesis) + 1))
    for i, ref in enumerate(reference, start=1):
        current = [i]
        for j, hyp in enumerate(hypothesis, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ref != hyp)))
        previous = current
    return previous[-1]


@dataclass(frozen=True)
class Counts:
    word_errors: int
    words: int
    char_errors: int
    chars: int

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(
            self.word_errors + other.word_errors,
            self.words + other.words,
            self.char_errors + other.char_errors,
            self.chars + other.chars,
        )

    @property
    def wer(self) -> float:
        return self.word_errors / self.words if self.words else 0.0

    @property
    def cer(self) -> float:
        return self.char_errors / self.chars if self.chars else 0.0


def count(reference: str, hypothesis: str) -> Counts:
    ref, hyp = normalize(reference), normalize(hypothesis)
    ref_chars, hyp_chars = list(ref.replace(" ", "")), list(hyp.replace(" ", ""))
    return Counts(
        word_errors=edit_distance(ref.split(), hyp.split()),
        words=len(ref.split()),
        char_errors=edit_distance(ref_chars, hyp_chars),
        chars=len(ref_chars),
    )


def evaluate(rows: list[dict[str, str]]) -> dict[str, Counts]:
    """Totaux globaux (corpus, pas moyenne des phrases) et par locuteur et condition."""
    totals: dict[str, Counts] = defaultdict(lambda: Counts(0, 0, 0, 0))
    for row in rows:
        if not normalize(row["reference"]):
            raise ValueError(f"{row['id']} : référence vide")
        c = count(row["reference"], row.get("hypothesis", ""))
        totals["global"] += c
        for key in ("speaker", "condition"):
            if row.get(key):
                totals[f"{key}={row[key]}"] += c
    return dict(totals)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.results.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for name, c in sorted(evaluate(rows).items(), key=lambda kv: kv[0] != "global"):
        print(f"{name:30} WER {c.wer:6.1%}  CER {c.cer:6.1%}  ({c.words} mots)")


if __name__ == "__main__":
    main()
