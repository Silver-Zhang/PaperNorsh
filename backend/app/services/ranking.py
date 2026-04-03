from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.preference import UserPreference
    from app.services.sources.base import RawPaper

logger = logging.getLogger(__name__)


class RelevanceRanker:
    """Score papers against a user's preferences and explain why."""

    def score_paper(
        self,
        paper: "RawPaper",
        preference: "UserPreference",
    ) -> tuple[float, dict]:
        """Return (total_score, breakdown_dict).

        Scoring rules
        -------------
        +10 per keyword found in title
        +5  per keyword found in abstract
        -20 per exclude_keyword found in title or abstract
        +15 per followed author matched in paper authors
        +5  if paper.source is in preferred_sources
        +10 per preferred_journal matched against paper.journal_name
        Score is clamped to a minimum of 0.
        """
        breakdown: dict[str, list | float] = {
            "keyword_title_hits": [],
            "keyword_abstract_hits": [],
            "exclude_keyword_hits": [],
            "author_hits": [],
            "source_bonus": 0.0,
            "journal_hits": [],
        }

        title_lower = (paper.title or "").lower()
        abstract_lower = (paper.abstract or "").lower()
        paper_authors_lower = [
            a.get("name", "").lower() for a in (paper.authors or [])
        ]

        raw_score = 0.0

        # Keywords
        for kw in preference.keywords or []:
            kw_lower = kw.lower()
            if kw_lower in title_lower:
                raw_score += 10.0
                breakdown["keyword_title_hits"].append(kw)
            elif kw_lower in abstract_lower:
                raw_score += 5.0
                breakdown["keyword_abstract_hits"].append(kw)

        # Exclude keywords
        for ekw in preference.exclude_keywords or []:
            ekw_lower = ekw.lower()
            if ekw_lower in title_lower or ekw_lower in abstract_lower:
                raw_score -= 20.0
                breakdown["exclude_keyword_hits"].append(ekw)

        # Followed authors
        for author in preference.follow_authors or []:
            author_lower = author.lower()
            if any(author_lower in pa for pa in paper_authors_lower):
                raw_score += 15.0
                breakdown["author_hits"].append(author)

        # Preferred source
        if paper.source in (preference.preferred_sources or []):
            raw_score += 5.0
            breakdown["source_bonus"] = 5.0

        # Preferred journals
        journal_lower = (paper.journal_name or "").lower()
        for journal in preference.preferred_journals or []:
            if journal.lower() in journal_lower:
                raw_score += 10.0
                breakdown["journal_hits"].append(journal)

        total_score = max(0.0, raw_score)
        breakdown["raw_score"] = raw_score
        breakdown["total_score"] = total_score

        logger.debug(
            "Scored paper %r: %.1f (raw=%.1f)",
            paper.title[:50],
            total_score,
            raw_score,
        )
        return total_score, breakdown
