"""Corpus, dictionnaire, provenance, révisions et exports

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ENUMS = {
    "script": ("Latn", "Tfng"),
    "source_kind": (
        "contribution",
        "interview",
        "recording",
        "publication",
        "dictionary",
        "dataset",
        "other",
    ),
    "content_status": ("raw", "pending", "validated", "restricted", "withdrawn"),
    "dataset_purpose": ("training", "publication"),
}


def enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*ENUMS[name], name=name, create_type=False)


# Garanties en base, indépendantes du code applicatif : la forme d'origine d'une entrée ou d'un
# texte ne peut pas être modifiée, et le journal des révisions ne peut être ni modifié ni effacé.


def upgrade() -> None:
    bind = op.get_bind()
    for name in ENUMS:
        enum(name).create(bind, checkfirst=False)

    op.create_table(
        "orthography_conventions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("script", enum("script"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("kind", enum("source_kind"), nullable=False),
        sa.Column("citation", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("rights_holder", sa.Text(), nullable=True),
        sa.Column("license", sa.Text(), nullable=False),
        sa.Column("license_allows_training", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "api_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_table(
        "corpus_texts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("script", enum("script"), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("tifinagh_text", sa.Text(), nullable=True),
        sa.Column("translation_fr", sa.Text(), nullable=True),
        sa.Column("translation_en", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("variant", sa.Text(), nullable=True),
        sa.Column("collected_on", sa.Date(), nullable=True),
        sa.Column("license", sa.Text(), nullable=False),
        sa.Column("consent_reference", sa.Text(), nullable=True),
        sa.Column("allow_publication", sa.Boolean(), nullable=False),
        sa.Column("allow_training", sa.Boolean(), nullable=False),
        sa.Column("distribution_restrictions", sa.Text(), nullable=True),
        sa.Column("status", enum("content_status"), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("contributor_id", sa.Uuid(), nullable=True),
        sa.Column("validated_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["contributor_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
        ),
        sa.ForeignKeyConstraint(
            ["validated_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("purpose", enum("dataset_purpose"), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "lexical_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("headword", sa.Text(), nullable=False),
        sa.Column("headword_script", enum("script"), nullable=False),
        sa.Column("headword_key", sa.Text(), nullable=False),
        sa.Column("part_of_speech", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("variant", sa.Text(), nullable=True),
        sa.Column("collected_on", sa.Date(), nullable=True),
        sa.Column("license", sa.Text(), nullable=False),
        sa.Column("consent_reference", sa.Text(), nullable=True),
        sa.Column("allow_publication", sa.Boolean(), nullable=False),
        sa.Column("allow_training", sa.Boolean(), nullable=False),
        sa.Column("distribution_restrictions", sa.Text(), nullable=True),
        sa.Column("status", enum("content_status"), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("contributor_id", sa.Uuid(), nullable=True),
        sa.Column("validated_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["contributor_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
        ),
        sa.ForeignKeyConstraint(
            ["validated_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_lexical_entries_headword_key"), "lexical_entries", ["headword_key"], unique=False
    )
    op.create_table(
        "revisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column(
            "at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_revisions_entity_id"), "revisions", ["entity_id"], unique=False)
    op.create_table(
        "dataset_items",
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
        ),
        sa.PrimaryKeyConstraint("dataset_id", "entity", "entity_id"),
    )
    op.create_index(
        op.f("ix_dataset_items_entity_id"), "dataset_items", ["entity_id"], unique=False
    )
    op.create_table(
        "lexical_senses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entry_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("definition_fr", sa.Text(), nullable=True),
        sa.Column("definition_en", sa.Text(), nullable=True),
        sa.Column("translation_fr", sa.Text(), nullable=True),
        sa.Column("translation_en", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            ["lexical_entries.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "lexical_spellings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entry_id", sa.Uuid(), nullable=False),
        sa.Column("form", sa.Text(), nullable=False),
        sa.Column("form_key", sa.Text(), nullable=False),
        sa.Column("script", enum("script"), nullable=False),
        sa.Column("convention_id", sa.Uuid(), nullable=True),
        sa.Column("validated_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["convention_id"],
            ["orthography_conventions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            ["lexical_entries.id"],
        ),
        sa.ForeignKeyConstraint(
            ["validated_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entry_id", "script", "form"),
    )
    op.create_index(
        op.f("ix_lexical_spellings_form_key"), "lexical_spellings", ["form_key"], unique=False
    )
    op.create_table(
        "lexical_examples",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sense_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("script", enum("script"), nullable=False),
        sa.Column("translation_fr", sa.Text(), nullable=True),
        sa.Column("translation_en", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["sense_id"],
            ["lexical_senses.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    for table, column in (("lexical_entries", "headword"), ("corpus_texts", "original_text")):
        op.execute(f"""
            CREATE FUNCTION {table}_keep_original() RETURNS trigger AS $$
            BEGIN
              IF NEW.{column} IS DISTINCT FROM OLD.{column} THEN
                RAISE EXCEPTION '{table}.{column} : la forme d''origine ne peut pas être modifiée';
              END IF;
              RETURN NEW;
            END $$ LANGUAGE plpgsql;
            CREATE TRIGGER {table}_keep_original BEFORE UPDATE ON {table}
              FOR EACH ROW EXECUTE FUNCTION {table}_keep_original();
        """)
    op.execute("""
        CREATE FUNCTION revisions_append_only() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'le journal des révisions ne peut être ni modifié ni effacé';
        END $$ LANGUAGE plpgsql;
        CREATE TRIGGER revisions_append_only BEFORE UPDATE OR DELETE ON revisions
          FOR EACH ROW EXECUTE FUNCTION revisions_append_only();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER revisions_append_only ON revisions")
    op.execute("DROP FUNCTION revisions_append_only()")
    for table in ("lexical_entries", "corpus_texts"):
        op.execute(f"DROP TRIGGER {table}_keep_original ON {table}")
        op.execute(f"DROP FUNCTION {table}_keep_original()")
    op.drop_table("lexical_examples")
    op.drop_index(op.f("ix_lexical_spellings_form_key"), table_name="lexical_spellings")
    op.drop_table("lexical_spellings")
    op.drop_table("lexical_senses")
    op.drop_index(op.f("ix_dataset_items_entity_id"), table_name="dataset_items")
    op.drop_table("dataset_items")
    op.drop_index(op.f("ix_revisions_entity_id"), table_name="revisions")
    op.drop_table("revisions")
    op.drop_index(op.f("ix_lexical_entries_headword_key"), table_name="lexical_entries")
    op.drop_table("lexical_entries")
    op.drop_table("datasets")
    op.drop_table("corpus_texts")
    op.drop_table("api_tokens")
    op.drop_table("sources")
    op.drop_table("orthography_conventions")
    bind = op.get_bind()
    for name in reversed(list(ENUMS)):
        enum(name).drop(bind, checkfirst=False)
