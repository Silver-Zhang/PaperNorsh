import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    doi: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, unique=False)
    arxiv_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    published_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    journal_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    venue: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    raw_metadata: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    # Deduplication hash = md5(title.lower().strip())
    dedup_hash: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)

    # relationships
    interactions: Mapped[list["PaperInteraction"]] = relationship(
        "PaperInteraction", back_populates="paper", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Paper id={self.id} source={self.source} title={self.title[:40]!r}>"


class PaperInteraction(Base):
    __tablename__ = "paper_interactions"
    __table_args__ = (UniqueConstraint("user_id", "paper_id", name="uq_user_paper"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # saved / ignored / highly_relevant
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    user: Mapped["User"] = relationship("User", back_populates="paper_interactions")  # noqa: F821
    paper: Mapped["Paper"] = relationship("Paper", back_populates="interactions")

    def __repr__(self) -> str:
        return f"<PaperInteraction user={self.user_id} paper={self.paper_id} action={self.action}>"
