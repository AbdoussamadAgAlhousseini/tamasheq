"""Bibliothèque des savoirs : documents, niveaux d'accès, passages indexés

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_ENUMS = {
    "knowledge_theme": (
        "oral_history",
        "proverbs",
        "culture",
        "pastoralism",
        "environment",
        "plants",
        "toponymy",
        "crafts",
        "intergenerational",
        "language",
    ),
    "access_level": ("public", "community", "restricted"),
}


def enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*NEW_ENUMS[name], name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for name in NEW_ENUMS:
        enum(name).create(bind, checkfirst=False)

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("theme", enum("knowledge_theme"), nullable=False),
        sa.Column("access_level", enum("access_level"), nullable=False),
        sa.Column("author_credit", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("variant", sa.Text(), nullable=True),
        sa.Column("collected_on", sa.Date(), nullable=True),
        sa.Column("license", sa.Text(), nullable=False),
        sa.Column("consent_reference", sa.Text(), nullable=True),
        sa.Column("allow_publication", sa.Boolean(), nullable=False),
        sa.Column("allow_training", sa.Boolean(), nullable=False),
        sa.Column("distribution_restrictions", sa.Text(), nullable=True),
        sa.Column(
            "status", postgresql.ENUM(name="content_status", create_type=False), nullable=False
        ),
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
        "knowledge_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple'::regconfig, text)", persisted=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["knowledge_documents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_chunks_tsv", "knowledge_chunks", ["tsv"], unique=False, postgresql_using="gin"
    )

    op.execute("""
        CREATE FUNCTION knowledge_documents_keep_original() RETURNS trigger AS $$
        BEGIN
          IF NEW.body IS DISTINCT FROM OLD.body THEN
            RAISE EXCEPTION
              'knowledge_documents.body : la forme d''origine ne peut pas être modifiée';
          END IF;
          RETURN NEW;
        END $$ LANGUAGE plpgsql;
        CREATE TRIGGER knowledge_documents_keep_original BEFORE UPDATE ON knowledge_documents
          FOR EACH ROW EXECUTE FUNCTION knowledge_documents_keep_original();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER knowledge_documents_keep_original ON knowledge_documents")
    op.execute("DROP FUNCTION knowledge_documents_keep_original()")
    op.drop_index("ix_knowledge_chunks_tsv", table_name="knowledge_chunks", postgresql_using="gin")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    bind = op.get_bind()
    for name in reversed(list(NEW_ENUMS)):
        enum(name).drop(bind, checkfirst=False)
