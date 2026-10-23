"""Outils d'administration en ligne de commande.

    uv run python -m app.cli <commande> --help

Les imports sont tout ou rien : le fichier entier est vérifié avant d'écrire quoi que ce soit,
et les contenus importés arrivent au statut « brut » (jamais « validé »).
"""

import argparse
import json
import sys
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import issue_token
from app.db import get_engine
from app.governance import Content, GovernanceError, withdraw
from app.models import (
    ApiToken,
    CorpusText,
    DatasetPurpose,
    KnowledgeDocument,
    LexicalEntry,
    OrthographyConvention,
    Role,
    Script,
    Source,
    SourceKind,
    Status,
    User,
)
from app.schemas import CorpusTextIn, KnowledgeDocumentIn, LexicalEntryIn
from app.services import corpus, datasets, knowledge, lexicon

MODELS: dict[str, type[LexicalEntry] | type[CorpusText] | type[KnowledgeDocument]] = {
    "lexicon": LexicalEntry,
    "corpus": CorpusText,
    "knowledge": KnowledgeDocument,
}
EXPORTABLE = ("lexicon", "corpus")


def fail(message: str) -> NoReturn:
    sys.exit(f"Erreur : {message}")


def user_by_email(session: Session, email: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        fail(f"utilisateur inconnu : {email}")
    return user


def create_user(session: Session, a: argparse.Namespace) -> None:
    user = User(email=a.email, pseudonym=a.pseudonym, role=Role(a.role))
    session.add(user)
    session.flush()
    token = issue_token(session, user)
    print(f"Utilisateur {a.pseudonym} ({a.role}) créé.")
    print(f"Jeton (affiché une seule fois, à transmettre de façon sûre) : {token}")


def new_token(session: Session, a: argparse.Namespace) -> None:
    token = issue_token(session, user_by_email(session, a.email))
    print(f"Nouveau jeton (affiché une seule fois) : {token}")


def revoke_tokens(session: Session, a: argparse.Namespace) -> None:
    user = user_by_email(session, a.email)
    tokens = session.scalars(
        select(ApiToken).where(ApiToken.user_id == user.id, ApiToken.revoked_at.is_(None))
    ).all()
    for token in tokens:
        token.revoked_at = datetime.now(UTC)
    print(f"{len(tokens)} jeton(s) révoqué(s).")


def add_source(session: Session, a: argparse.Namespace) -> None:
    source = Source(
        title=a.title,
        kind=SourceKind(a.kind),
        license=a.license,
        license_allows_training={"yes": True, "no": False, "unknown": None}[a.training],
        citation=a.citation,
        url=a.url,
        rights_holder=a.rights_holder,
        notes=a.notes,
    )
    session.add(source)
    session.flush()
    print(f"Source créée : {source.id}")


def add_convention(session: Session, a: argparse.Namespace) -> None:
    convention = OrthographyConvention(
        name=a.name, script=Script(a.script), description=a.description, reference=a.reference
    )
    session.add(convention)
    session.flush()
    print(f"Convention créée : {convention.id}")


def read_jsonl[T: BaseModel](path: Path, schema: type[T]) -> list[T]:
    items: list[T] = []
    errors: list[str] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            items.append(schema.model_validate_json(line))
        except ValidationError as e:
            details = "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())
            errors.append(f"ligne {n} : {details}")
    if errors:
        fail("fichier refusé, rien n'a été importé.\n" + "\n".join(errors))
    return items


def import_file(session: Session, a: argparse.Namespace) -> None:
    source = session.get(Source, uuid.UUID(a.source))
    if source is None:
        fail(f"source inconnue : {a.source}")
    actor = user_by_email(session, a.actor) if a.actor else None
    if a.kind == "lexicon":
        entries = read_jsonl(Path(a.file), LexicalEntryIn)
        for entry in entries:
            lexicon.create_entry(session, entry, source, actor, Status.RAW)
        count = len(entries)
    elif a.kind == "corpus":
        texts = read_jsonl(Path(a.file), CorpusTextIn)
        for text in texts:
            corpus.create_text(session, text, source, actor, Status.RAW)
        count = len(texts)
    else:
        documents = read_jsonl(Path(a.file), KnowledgeDocumentIn)
        for document in documents:
            knowledge.create_document(session, document, source, actor, Status.RAW)
        count = len(documents)
    print(f"{count} élément(s) importé(s) au statut « brut », à faire valider.")


def export(session: Session, a: argparse.Namespace) -> None:
    actor = user_by_email(session, a.actor) if a.actor else None
    dataset, content = datasets.export(session, a.kind, DatasetPurpose(a.purpose), a.name, actor)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{a.name}.jsonl").write_text(content, encoding="utf-8")
    manifest = {
        "id": str(dataset.id),
        "name": dataset.name,
        "kind": dataset.kind,
        "purpose": dataset.purpose.value,
        "criteria": dataset.criteria,
        "item_count": dataset.item_count,
        "sha256": dataset.file_sha256,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (out / f"{a.name}.manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{dataset.item_count} éléments exportés dans {out / f'{a.name}.jsonl'}")


def _withdraw_all(session: Session, items: list[Content], actor: User, reason: str) -> None:
    for item in items:
        try:
            used = withdraw(session, item, actor, reason)
        except GovernanceError as e:
            fail(f"{item.id} : {e}")
        names = ", ".join(d.name for d in used) or "aucun"
        print(f"Retiré : {item.id} — exports concernés : {names}")


def withdraw_one(session: Session, a: argparse.Namespace) -> None:
    key = uuid.UUID(a.id)
    item: Content | None
    if a.kind == "lexicon":
        item = session.get(LexicalEntry, key)
    elif a.kind == "corpus":
        item = session.get(CorpusText, key)
    else:
        item = session.get(KnowledgeDocument, key)
    if item is None:
        fail("contenu introuvable")
    _withdraw_all(session, [item], user_by_email(session, a.actor), a.reason)


def withdraw_contributor(session: Session, a: argparse.Namespace) -> None:
    contributor = user_by_email(session, a.email)
    items: list[Content] = []
    for model in MODELS.values():
        items += session.scalars(
            select(model).where(
                model.contributor_id == contributor.id, model.status != Status.WITHDRAWN
            )
        )
    _withdraw_all(session, items, user_by_email(session, a.actor), a.reason)
    print(f"{len(items)} contenu(s) retiré(s).")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__)
    sub = p.add_subparsers(required=True)

    def command(
        name: str, fn: Callable[[Session, argparse.Namespace], None], help: str
    ) -> argparse.ArgumentParser:
        c = sub.add_parser(name, help=help)
        c.set_defaults(fn=fn)
        return c

    c = command("create-user", create_user, "créer un compte et son premier jeton")
    c.add_argument("--email", required=True)
    c.add_argument("--pseudonym", required=True)
    c.add_argument("--role", choices=[r.value for r in Role], required=True)

    c = command("new-token", new_token, "émettre un jeton supplémentaire")
    c.add_argument("--email", required=True)

    c = command("revoke-tokens", revoke_tokens, "révoquer tous les jetons d'un compte")
    c.add_argument("--email", required=True)

    c = command("add-source", add_source, "enregistrer une source et ses droits")
    c.add_argument("--title", required=True)
    c.add_argument("--kind", choices=[k.value for k in SourceKind], required=True)
    c.add_argument("--license", required=True, help="identifiant SPDX ou texte de l'accord")
    c.add_argument(
        "--training",
        choices=["yes", "no", "unknown"],
        required=True,
        help="la licence ou l'accord autorise-t-il l'entraînement de modèles ?",
    )
    for opt in ("--citation", "--url", "--rights-holder", "--notes"):
        c.add_argument(opt)

    c = command("add-convention", add_convention, "enregistrer une convention orthographique")
    c.add_argument("--name", required=True)
    c.add_argument("--script", choices=[s.value for s in Script], required=True)
    c.add_argument("--description")
    c.add_argument("--reference")

    c = command("import", import_file, "importer un fichier JSONL (statut « brut »)")
    c.add_argument("kind", choices=list(MODELS))
    c.add_argument("file")
    c.add_argument("--source", required=True, help="identifiant de la source")
    c.add_argument("--actor", help="e-mail de la personne qui importe")

    c = command("export", export, "produire un export figé et traçable")
    c.add_argument("kind", choices=EXPORTABLE)
    c.add_argument("--purpose", choices=[d.value for d in DatasetPurpose], required=True)
    c.add_argument("--name", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--actor")

    c = command("withdraw", withdraw_one, "retirer un contenu")
    c.add_argument("kind", choices=list(MODELS))
    c.add_argument("id")
    c.add_argument("--reason", required=True)
    c.add_argument("--actor", required=True)

    c = command(
        "withdraw-contributor",
        withdraw_contributor,
        "retirer toutes les contributions d'une personne",
    )
    c.add_argument("--email", required=True)
    c.add_argument("--reason", required=True)
    c.add_argument("--actor", required=True)
    return p


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    with Session(get_engine()) as session, session.begin():
        args.fn(session, args)


if __name__ == "__main__":
    main()
