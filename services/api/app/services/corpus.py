from sqlalchemy.orm import Session

from app.governance import record
from app.models import CorpusText, Source, Status, User
from app.schemas import CorpusTextIn, resolved


def create_text(
    session: Session, data: CorpusTextIn, source: Source, actor: User | None, status: Status
) -> CorpusText:
    text = CorpusText(
        original_text=data.text,
        normalized_text=data.text,
        script=resolved(data.script),
        source_id=source.id,
        contributor_id=actor.id if actor and status != Status.RAW else None,
        status=status,
        **data.model_dump(exclude={"text", "script"}),
    )
    session.add(text)
    record(session, text, "create", actor, None)
    return text
