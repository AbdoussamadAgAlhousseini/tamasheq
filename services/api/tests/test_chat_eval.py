import asyncio
import csv
import json
from pathlib import Path

import pytest

from app.ai.chat import ChatMessage, ChatProviderError, ChatReply
from app.evaluation.chat_eval import RATING_COLUMNS, load_questions, run, write_csv


class ScriptedProvider:
    name = "fake"

    async def reply(self, messages: list[ChatMessage]) -> ChatReply:
        assert len(messages) == 1  # une conversation neuve par question
        if messages[0].content == "refus":
            raise ChatProviderError("refused", "test")
        return ChatReply(text="r", provider="fake", model="m1", truncated=False)


def write_jsonl(path: Path, items: list[dict[str, str]]) -> Path:
    path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in items), encoding="utf-8")
    return path


def q(id_: str, question: str = "Question ?") -> dict[str, str]:
    return {"id": id_, "category": "c", "language": "fr", "question": question}


def test_run_and_csv(tmp_path: Path) -> None:
    questions = load_questions(write_jsonl(tmp_path / "q.jsonl", [q("a"), q("b", "refus")]))
    rows = asyncio.run(run(questions, ScriptedProvider()))
    assert [(r["id"], r["reply"], r["error"]) for r in rows] == [
        ("a", "r", ""),
        ("b", "", "refused"),
    ]
    assert all(r[c] == "" for r in rows for c in RATING_COLUMNS)

    out = tmp_path / "res" / "x.csv"
    write_csv(rows, out)
    with out.open(encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 2


@pytest.mark.parametrize(
    "items",
    [[{"id": "a", "category": "c", "language": "fr"}], [q("a"), q("a")]],
)
def test_invalid_question_files(tmp_path: Path, items: list[dict[str, str]]) -> None:
    with pytest.raises(ValueError):
        load_questions(write_jsonl(tmp_path / "q.jsonl", items))
