from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.services.sources.base import PaperSource, RawPaper

logger = logging.getLogger(__name__)

_OPENALEX_BASE = "https://api.openalex.org/works"
_REQUEST_INTERVAL = 1.0  # seconds between requests (unauthenticated rate limit)


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


class OpenAlexSource(PaperSource):
    def __init__(self) -> None:
        self._last_request: float = 0.0

    @property
    def name(self) -> str:
        return "openalex"

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < _REQUEST_INTERVAL:
            time.sleep(_REQUEST_INTERVAL - elapsed)
        self._last_request = time.monotonic()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def fetch_recent(self, keywords: list[str], max_results: int) -> list[RawPaper]:
        if not keywords:
            logger.warning("OpenAlexSource: no keywords provided, skipping fetch")
            return []

        since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        search_query = " OR ".join(keywords)
        params = {
            "search": search_query,
            "filter": f"from_publication_date:{since}",
            "per-page": min(max_results, 200),
            "select": "id,title,authorships,abstract_inverted_index,doi,primary_location,publication_date,concepts,biblio",
        }

        self._throttle()
        logger.info("OpenAlexSource fetching with query=%r", search_query)

        with httpx.Client(timeout=30) as client:
            resp = client.get(_OPENALEX_BASE, params=params)
            resp.raise_for_status()

        data = resp.json()
        results = data.get("results", [])

        papers: list[RawPaper] = []
        for item in results:
            try:
                papers.append(self._parse_item(item))
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("OpenAlexSource: failed to parse item: %s", exc, exc_info=True)

        logger.info("OpenAlexSource: fetched %d papers", len(papers))
        return papers

    # ------------------------------------------------------------------

    def _parse_item(self, item: dict) -> RawPaper:
        oa_id = item.get("id", "")
        source_id = oa_id.split("/")[-1] if oa_id else ""

        authors = [
            {
                "name": a.get("author", {}).get("display_name", ""),
                "affiliation": (a.get("institutions") or [{}])[0].get("display_name"),
            }
            for a in item.get("authorships", [])
        ]

        # Reconstruct abstract from inverted index
        abstract = _reconstruct_abstract(item.get("abstract_inverted_index"))

        doi_raw = item.get("doi", "")
        doi = doi_raw.replace("https://doi.org/", "").replace("http://dx.doi.org/", "") if doi_raw else None

        location = item.get("primary_location") or {}
        source_info = location.get("source") or {}
        journal_name = source_info.get("display_name")
        url = location.get("landing_page_url") or (f"https://doi.org/{doi}" if doi else oa_id)

        keywords = [c.get("display_name", "") for c in item.get("concepts", []) if c.get("score", 0) > 0.3]

        return RawPaper(
            title=(item.get("title") or "").strip(),
            source=self.name,
            source_id=source_id,
            url=url,
            authors=authors,
            abstract=abstract,
            doi=doi,
            published_date=_parse_date(item.get("publication_date")),
            journal_name=journal_name,
            keywords=keywords,
            raw_metadata={"id": oa_id, "biblio": item.get("biblio")},
        )


def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
    if not inverted_index:
        return None
    words: list[str] = [""] * (max(pos for positions in inverted_index.values() for pos in positions) + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(w for w in words if w) or None
