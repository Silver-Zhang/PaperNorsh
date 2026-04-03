from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.digest import DailyDigest
from app.models.paper import Paper
from app.models.preference import UserPreference
from app.models.user import User
from app.services.ranking import RelevanceRanker
from app.services.sources.arxiv import ArxivSource
from app.services.sources.base import RawPaper
from app.services.sources.crossref import CrossrefSource
from app.services.sources.openalex import OpenAlexSource

logger = logging.getLogger(__name__)

ranker = RelevanceRanker()


def _dedup_hash(title: str) -> str:
    return hashlib.md5(title.lower().strip().encode()).hexdigest()


def _upsert_paper(db: Session, raw: RawPaper) -> Paper | None:
    """Persist a RawPaper, skipping duplicates. Returns the Paper or None on error."""
    if not raw.title or not raw.title.strip():
        return None

    h = _dedup_hash(raw.title)
    existing = db.query(Paper).filter(Paper.dedup_hash == h).first()
    if existing:
        return existing

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
    except IntegrityError:
        db.rollback()
        existing = db.query(Paper).filter(Paper.dedup_hash == h).first()
        return existing
    return paper


class DigestService:
    def __init__(self) -> None:
        self._sources = [ArxivSource(), OpenAlexSource(), CrossrefSource()]

    def generate_digest(self, user_id: uuid.UUID, db: Session) -> DailyDigest:
        today = date.today()

        # Check for existing digest
        existing = (
            db.query(DailyDigest)
            .filter(DailyDigest.user_id == user_id, DailyDigest.date == today)
            .first()
        )
        if existing and existing.status == "sent":
            logger.info("Digest already sent for user %s on %s", user_id, today)
            return existing

        # Create / reset digest record
        if existing is None:
            digest = DailyDigest(user_id=user_id, date=today, status="generating")
            db.add(digest)
            db.flush()
        else:
            digest = existing
            digest.status = "generating"
            digest.updated_at = datetime.now(timezone.utc)
            db.flush()

        try:
            pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
            if pref is None:
                pref = UserPreference(user_id=user_id)
                db.add(pref)
                db.flush()

            keywords = pref.keywords or []
            max_papers = pref.max_papers_per_digest

            # Fetch from active sources
            all_raw: list[RawPaper] = []
            for source in self._sources:
                if source.name in (pref.preferred_sources or []):
                    try:
                        results = source.fetch_recent(keywords, max_results=100)
                        all_raw.extend(results)
                    except Exception as exc:  # pylint: disable=broad-except
                        logger.error("Source %s failed: %s", source.name, exc, exc_info=True)

            # Persist papers
            papers_in_db: list[tuple[Paper, RawPaper]] = []
            for raw in all_raw:
                p = _upsert_paper(db, raw)
                if p:
                    papers_in_db.append((p, raw))

            db.flush()

            # Score
            scored: list[tuple[float, Paper]] = []
            for paper_obj, raw_paper in papers_in_db:
                score, _ = ranker.score_paper(raw_paper, pref)
                scored.append((score, paper_obj))

            scored.sort(key=lambda x: x[0], reverse=True)
            top = scored[:max_papers]

            digest.papers = [
                {"paper_id": str(p.id), "relevance_score": s, "rank": rank + 1}
                for rank, (s, p) in enumerate(top)
            ]
            digest.status = "pending"  # email not yet sent
            digest.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(digest)
            logger.info(
                "Digest generated for user %s: %d papers", user_id, len(digest.papers)
            )
            return digest

        except Exception:
            digest.status = "failed"
            digest.updated_at = datetime.now(timezone.utc)
            db.commit()
            raise
