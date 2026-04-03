from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.services.sources.base import PaperSource, RawPaper

from app.core.config import settings

logger = logging.getLogger(__name__)

_CROSSREF_BASE = "https://api.crossref.org/works"


def _parse_date(date_parts: list | None) -> date | None:
    if not date_parts:
        return None
    parts = date_parts[0] if date_parts else []
    try:
        if len(parts) >= 3:
            return date(parts[0], parts[1], parts[2])
        if len(parts) == 2:
            return date(parts[0], parts[1], 1)
        if len(parts) == 1:
            return date(parts[0], 1, 1)
    except (TypeError, ValueError):
        pass
    return None


class CrossrefSource(PaperSource):
    @property
    def name(self) -> str:
        return "crossref"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def fetch_recent(self, keywords: list[str], max_results: int) -> list[RawPaper]:
        if not keywords:
            logger.warning("CrossrefSource: no keywords provided, skipping fetch")
            return []

        since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        query = " ".join(keywords)
        params = {
            "query": query,
            "filter": f"from-pub-date:{since}",
            "rows": min(max_results, 1000),
            "sort": "published",
            "order": "desc",
            "mailto": settings.CROSSREF_MAILTO,
        }

        logger.info("CrossrefSource fetching with query=%r", query)
        with httpx.Client(timeout=30) as client:
            resp = client.get(_CROSSREF_BASE, params=params)
            resp.raise_for_status()

        data = resp.json()
        items = data.get("message", {}).get("items", [])

        papers: list[RawPaper] = []
        for item in items:
            try:
                papers.append(self._parse_item(item))
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("CrossrefSource: failed to parse item: %s", exc, exc_info=True)

        logger.info("CrossrefSource: fetched %d papers", len(papers))
        return papers

    # ------------------------------------------------------------------

    def _parse_item(self, item: dict) -> RawPaper:
        doi = item.get("DOI", "")
        source_id = doi or item.get("URL", "")

        authors = []
        for a in item.get("author", []):
            name_parts = filter(None, [a.get("given"), a.get("family")])
            authors.append(
                {
                    "name": " ".join(name_parts),
                    "affiliation": (a.get("affiliation") or [{}])[0].get("name"),
                }
            )

        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""

        abstract = item.get("abstract", None)
        if abstract:
            # Strip JATS XML tags
            import re
            abstract = re.sub(r"<[^>]+>", "", abstract).strip() or None

        container = item.get("container-title", [])
        journal_name = container[0] if container else None

        published = _parse_date(
            item.get("published-print", {}).get("date-parts")
            or item.get("published-online", {}).get("date-parts")
        )

        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")

        keywords = item.get("subject", [])

        return RawPaper(
            title=title.strip(),
            source=self.name,
            source_id=source_id,
            url=url,
            authors=authors,
            abstract=abstract,
            doi=doi or None,
            published_date=published,
            journal_name=journal_name,
            keywords=keywords,
            raw_metadata={"DOI": doi, "type": item.get("type")},
        )
