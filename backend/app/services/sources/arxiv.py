from __future__ import annotations

import logging
import re
from datetime import date
from urllib.parse import quote_plus

import feedparser
from tenacity import retry, stop_after_attempt, wait_fixed

from app.services.sources.base import PaperSource, RawPaper

logger = logging.getLogger(__name__)

_ARXIV_BASE = "http://export.arxiv.org/api/query"


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def _extract_arxiv_id(entry_id: str) -> str:
    # e.g. http://arxiv.org/abs/2403.12345v1 -> 2403.12345
    parts = entry_id.rstrip("/").split("/")
    raw = parts[-1]
    return re.sub(r"v\d+$", "", raw)


class ArxivSource(PaperSource):
    @property
    def name(self) -> str:
        return "arxiv"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def fetch_recent(self, keywords: list[str], max_results: int) -> list[RawPaper]:
        if not keywords:
            logger.warning("ArxivSource: no keywords provided, skipping fetch")
            return []

        query = " OR ".join(f'all:"{kw}"' for kw in keywords)
        url = (
            f"{_ARXIV_BASE}?search_query={quote_plus(query)}"
            f"&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        )
        logger.info("ArxivSource fetching: %s", url)

        feed = feedparser.parse(url)
        if feed.bozo and feed.bozo_exception:
            logger.error("ArxivSource feed parse error: %s", feed.bozo_exception)

        papers: list[RawPaper] = []
        for entry in feed.entries:
            try:
                arxiv_id = _extract_arxiv_id(entry.get("id", ""))
                authors = [
                    {"name": a.get("name", ""), "affiliation": None}
                    for a in entry.get("authors", [])
                ]
                tags = [t.get("term", "") for t in entry.get("tags", []) if t.get("scheme") != "http://arxiv.org/schemas/atom"]
                published = _parse_date(entry.get("published", ""))
                doi = next(
                    (
                        link.get("href", "").replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
                        for link in entry.get("links", [])
                        if "doi" in link.get("href", "").lower()
                    ),
                    None,
                )
                papers.append(
                    RawPaper(
                        title=entry.get("title", "").replace("\n", " ").strip(),
                        source=self.name,
                        source_id=arxiv_id,
                        url=entry.get("link", f"https://arxiv.org/abs/{arxiv_id}"),
                        authors=authors,
                        abstract=entry.get("summary", "").replace("\n", " ").strip() or None,
                        doi=doi or None,
                        arxiv_id=arxiv_id,
                        published_date=published,
                        keywords=tags,
                        raw_metadata={
                            "id": entry.get("id"),
                            "categories": [t.get("term") for t in entry.get("tags", [])],
                        },
                    )
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("ArxivSource: failed to parse entry: %s", exc, exc_info=True)

        logger.info("ArxivSource: fetched %d papers", len(papers))
        return papers
