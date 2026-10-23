"""Enregistrements vocaux consentis

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-23 23:40:53.422310
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audio_recordings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Double(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("prompt_text_id", sa.Uuid(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("allow_voice_synthesis", sa.Boolean(), nullable=False),
        sa.Column("file_deleted_at", sa.DateTime(timezone=True), nullable=True),
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
            ["prompt_text_id"],
            ["corpus_texts.id"],
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
        sa.UniqueConstraint("storage_key"),
    )


def downgrade() -> None:
    op.drop_table("audio_recordings")
