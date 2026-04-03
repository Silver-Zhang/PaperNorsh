from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class RawPaper:
    """Normalised paper data returned by any source."""

    title: str
    source: str
    source_id: str
    url: str
    authors: list[dict] = field(default_factory=list)  # [{name, affiliation}]
    abstract: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    published_date: Optional[date] = None
    journal_name: Optional[str] = None
    venue: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    raw_metadata: Optional[dict] = None


class PaperSource(abc.ABC):
    """Abstract base class for all paper sources."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @abc.abstractmethod
    def fetch_recent(self, keywords: list[str], max_results: int) -> list[RawPaper]:
        """Fetch recent papers matching the given keywords."""
        ...
