"""Évaluation de la recherche documentaire (voir evaluation/knowledge/README.md).

    uv run python -m app.evaluation.retrieval_eval QUESTIONS.jsonl [--k 6]

Mesure, sans appeler de modèle, si les documents attendus figurent parmi les passages que
recevrait le modèle : rappel@k et rang réciproque moyen (MRR), au niveau des documents.
"""

import argparse
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import AccessLevel
from app.services.knowledge import search_chunks


@dataclass(frozen=True)
class Result:
    question_id: str
    recall: float
    reciprocal_rank: float


def evaluate(session: Session, path: Path, k: int) -> list[Result]:
    results: list[Result] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        expected = {uuid.UUID(i) for i in item["relevant_document_ids"]}
        hits = search_chunks(session, item["question"], [AccessLevel.PUBLIC], None, k)
        ranked = list(dict.fromkeys(h.chunk.document_id for h in hits))
        found = expected & set(ranked)
        first = next((i for i, d in enumerate(ranked, start=1) if d in expected), None)
        results.append(
            Result(
                question_id=item["id"],
                recall=len(found) / len(expected) if expected else 0.0,
                reciprocal_rank=1 / first if first else 0.0,
            )
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("questions", type=Path)
    parser.add_argument("--k", type=int, default=6)
    args = parser.parse_args()

    from app.db import get_engine

    with Session(get_engine()) as session:
        results = evaluate(session, args.questions, args.k)
    n = len(results) or 1
    print(f"{len(results)} questions, k={args.k}")
    print(f"rappel@{args.k} moyen : {sum(r.recall for r in results) / n:.2f}")
    print(f"MRR : {sum(r.reciprocal_rank for r in results) / n:.2f}")
    for r in results:
        if r.recall < 1:
            print(f"  {r.question_id} : rappel {r.recall:.2f}")


if __name__ == "__main__":
    main()
