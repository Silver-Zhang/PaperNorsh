from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.paper import Paper
from app.models.user import User
from app.services.digest import DigestService
from app.services.sources.base import RawPaper

if TYPE_CHECKING:
    from app.services.sources.base import PaperSource

logger = logging.getLogger(__name__)

_digest_service = DigestService()


def _dedup_hash(title: str) -> str:
    return hashlib.md5(title.lower().strip().encode()).hexdigest()


def fetch_and_store_papers(
    db: Session,
    sources: list["PaperSource"],
    keywords: list[str],
) -> list[Paper]:
    """Fetch papers from given sources, deduplicate, and persist to database."""
    stored: list[Paper] = []

    for source in sources:
        try:
            raw_papers = source.fetch_recent(keywords, max_results=100)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching from %s: %s", source.name, exc, exc_info=True)
            continue

        for raw in raw_papers:
            if not raw.title or not raw.title.strip():
                continue

            h = _dedup_hash(raw.title)
            existing = db.query(Paper).filter(Paper.dedup_hash == h).first()
            if existing:
                stored.append(existing)
                continue

            paper = Paper(
                title=raw.title,
                authors=raw.authors,
                abstract=raw.abstract,
                source=raw.source,
                source_id=raw.source_id,
                doi=raw.doi,
                arxiv_id=raw.arxiv_id,
                url=raw.url,
                published_date=raw.published_date,
                journal_name=raw.journal_name,
                venue=raw.venue,
                keywords=raw.keywords,
                raw_metadata=raw.raw_metadata,
                dedup_hash=h,
            )
            db.add(paper)
            try:
                db.flush()
                stored.append(paper)
            except IntegrityError:
                db.rollback()
                existing = db.query(Paper).filter(Paper.dedup_hash == h).first()
                if existing:
                    stored.append(existing)

    try:
        db.commit()
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error committing papers: %s", exc, exc_info=True)
        db.rollback()

    logger.info("fetch_and_store_papers: stored/found %d papers", len(stored))
    return stored


def generate_user_digest(user_id: uuid.UUID, db: Session):
    """Generate a daily digest for a single user."""
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        logger.warning("generate_user_digest: user %s not found or inactive", user_id)
        return None

    try:
        digest = _digest_service.generate_digest(user_id, db)
        return digest
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(
            "generate_user_digest failed for user %s: %s", user_id, exc, exc_info=True
        )
        return None
