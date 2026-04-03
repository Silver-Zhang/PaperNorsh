"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── papers ────────────────────────────────────────────────────────────────
    op.create_table(
        "papers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(512), nullable=False),
        sa.Column("doi", sa.String(512), nullable=True),
        sa.Column("arxiv_id", sa.String(128), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("journal_name", sa.String(512), nullable=True),
        sa.Column("venue", sa.String(512), nullable=True),
        sa.Column("keywords", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("raw_metadata", postgresql.JSON(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_summary_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("dedup_hash", sa.String(32), nullable=False),
    )
    op.create_index("ix_papers_source", "papers", ["source"])
    op.create_index("ix_papers_source_id", "papers", ["source_id"])
    op.create_index("ix_papers_published_date", "papers", ["published_date"])
    op.create_index("ix_papers_dedup_hash", "papers", ["dedup_hash"], unique=True)

    # ── user_preferences ──────────────────────────────────────────────────────
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("keywords", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("exclude_keywords", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("preferred_topics", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("follow_authors", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "preferred_sources",
            postgresql.JSON(),
            nullable=False,
            server_default='["arxiv","openalex","crossref"]',
        ),
        sa.Column("preferred_journals", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("delivery_time", sa.Time(), nullable=False, server_default="08:00:00"),
        sa.Column("max_papers_per_digest", sa.Integer(), nullable=False, server_default="20"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=True)

    # ── paper_interactions ────────────────────────────────────────────────────
    op.create_table(
        "paper_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "paper_id", name="uq_user_paper"),
    )
    op.create_index("ix_paper_interactions_user_id", "paper_interactions", ["user_id"])
    op.create_index("ix_paper_interactions_paper_id", "paper_interactions", ["paper_id"])

    # ── daily_digests ─────────────────────────────────────────────────────────
    op.create_table(
        "daily_digests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("papers", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "date", name="uq_user_date"),
    )
    op.create_index("ix_daily_digests_user_id", "daily_digests", ["user_id"])
    op.create_index("ix_daily_digests_date", "daily_digests", ["date"])


def downgrade() -> None:
    op.drop_table("daily_digests")
    op.drop_table("paper_interactions")
    op.drop_table("user_preferences")
    op.drop_table("papers")
    op.drop_table("users")
