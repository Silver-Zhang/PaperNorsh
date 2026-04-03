import uuid
from datetime import datetime, time, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    exclude_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_topics: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    follow_authors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_sources: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=lambda: ["arxiv", "openalex", "crossref"]
    )
    preferred_journals: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    delivery_time: Mapped[time] = mapped_column(
        Time, nullable=False, default=time(8, 0, 0)
    )
    max_papers_per_digest: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    user: Mapped["User"] = relationship("User", back_populates="preferences")  # noqa: F821

    def __repr__(self) -> str:
        return f"<UserPreference user_id={self.user_id}>"
