"""Tests for paper source fetchers with mocked HTTP/feed responses."""
from __future__ import annotations

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.sources.arxiv import ArxivSource
from app.services.sources.crossref import CrossrefSource
from app.services.sources.openalex import OpenAlexSource


# ─── Arxiv ────────────────────────────────────────────────────────────────────

ARXIV_FEED_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.99999v1</id>
    <title>Deep Learning Advances in 2024</title>
    <summary>We present new advances in deep learning architectures.</summary>
    <published>2024-01-15T00:00:00Z</published>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
    <link href="http://arxiv.org/abs/2401.99999v1" rel="alternate"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""


class TestArxivSource:
    def test_name(self):
        assert ArxivSource().name == "arxiv"

    def test_fetch_parses_correctly(self):
        import feedparser

        mock_feed = feedparser.parse(ARXIV_FEED_XML)
        with patch("app.services.sources.arxiv.feedparser.parse", return_value=mock_feed):
            source = ArxivSource()
            papers = source.fetch_recent(["deep learning"], max_results=10)

        assert len(papers) == 1
        p = papers[0]
        assert "Deep Learning" in p.title
        assert p.source == "arxiv"
        assert p.arxiv_id == "2401.99999"
        assert p.published_date == date(2024, 1, 15)
        assert len(p.authors) == 2
        assert p.authors[0]["name"] == "Alice Smith"
        assert "new advances" in (p.abstract or "")

    def test_fetch_returns_empty_for_no_keywords(self):
        source = ArxivSource()
        papers = source.fetch_recent([], max_results=10)
        assert papers == []

    def test_fetch_handles_malformed_entry_gracefully(self):
        """A bad entry should be skipped, not crash the whole fetch."""
        bad_feed = MagicMock()
        bad_feed.bozo = False
        bad_feed.bozo_exception = None
        # One bad entry with no 'id' or 'title'
        bad_entry = {}
        bad_feed.entries = [bad_entry]

        with patch("app.services.sources.arxiv.feedparser.parse", return_value=bad_feed):
            source = ArxivSource()
            papers = source.fetch_recent(["ml"], max_results=5)
        # Empty title entries are stored (or just no crash) — we verify no exception
        # The entry has no title so it gets an empty title paper or is filtered
        assert isinstance(papers, list)

    def test_fetch_strips_newlines_from_title(self):
        import feedparser

        xml = ARXIV_FEED_XML.replace(
            "Deep Learning Advances in 2024",
            "Deep Learning\nAdvances in 2024",
        )
        mock_feed = feedparser.parse(xml)
        with patch("app.services.sources.arxiv.feedparser.parse", return_value=mock_feed):
            papers = ArxivSource().fetch_recent(["deep learning"], max_results=5)
        assert "\n" not in papers[0].title


# ─── OpenAlex ─────────────────────────────────────────────────────────────────

_OA_RESPONSE = {
    "results": [
        {
            "id": "https://openalex.org/W2741809807",
            "title": "Attention Is All You Need",
            "authorships": [
                {
                    "author": {"display_name": "Ashish Vaswani"},
                    "institutions": [{"display_name": "Google Brain"}],
                }
            ],
            "abstract_inverted_index": {
                "The": [0],
                "dominant": [1],
                "sequence": [2],
                "transduction": [3],
                "models": [4],
            },
            "doi": "https://doi.org/10.48550/arXiv.1706.03762",
            "primary_location": {
                "landing_page_url": "https://arxiv.org/abs/1706.03762",
                "source": {"display_name": "arXiv"},
            },
            "publication_date": "2017-06-12",
            "concepts": [
                {"display_name": "Artificial intelligence", "score": 0.9},
                {"display_name": "Machine learning", "score": 0.8},
            ],
            "biblio": {"volume": None},
        }
    ]
}


class TestOpenAlexSource:
    def test_name(self):
        assert OpenAlexSource().name == "openalex"

    def test_fetch_parses_correctly(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _OA_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp

        with patch("app.services.sources.openalex.httpx.Client", return_value=mock_client):
            source = OpenAlexSource()
            with patch.object(source, "_throttle"):
                papers = source.fetch_recent(["attention", "transformer"], max_results=10)

        assert len(papers) == 1
        p = papers[0]
        assert p.title == "Attention Is All You Need"
        assert p.source == "openalex"
        assert p.source_id == "W2741809807"
        assert p.doi == "10.48550/arXiv.1706.03762"
        assert p.published_date == date(2017, 6, 12)
        assert p.authors[0]["name"] == "Ashish Vaswani"
        assert p.authors[0]["affiliation"] == "Google Brain"
        assert "Artificial intelligence" in p.keywords
        assert p.abstract is not None
        assert "dominant" in p.abstract

    def test_fetch_returns_empty_for_no_keywords(self):
        source = OpenAlexSource()
        papers = source.fetch_recent([], max_results=10)
        assert papers == []

    def test_reconstruct_abstract(self):
        from app.services.sources.openalex import _reconstruct_abstract

        inv_idx = {"Hello": [0], "world": [1], "test": [2]}
        result = _reconstruct_abstract(inv_idx)
        assert result == "Hello world test"

    def test_reconstruct_abstract_none(self):
        from app.services.sources.openalex import _reconstruct_abstract

        assert _reconstruct_abstract(None) is None
        assert _reconstruct_abstract({}) is None


# ─── Crossref ─────────────────────────────────────────────────────────────────

_CR_RESPONSE = {
    "message": {
        "items": [
            {
                "DOI": "10.1234/test.2024.001",
                "title": ["Advances in Quantum Computing"],
                "author": [
                    {"given": "Jane", "family": "Doe", "affiliation": [{"name": "MIT"}]},
                    {"given": "John", "family": "Smith", "affiliation": []},
                ],
                "abstract": "<jats:p>This paper studies <jats:bold>quantum</jats:bold> algorithms.</jats:p>",
                "container-title": ["Physical Review Letters"],
                "published-print": {"date-parts": [[2024, 3, 15]]},
                "URL": "https://doi.org/10.1234/test.2024.001",
                "subject": ["Quantum Physics", "Computer Science"],
                "type": "journal-article",
            }
        ]
    }
}


class TestCrossrefSource:
    def test_name(self):
        assert CrossrefSource().name == "crossref"

    def test_fetch_parses_correctly(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _CR_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp

        with patch("app.services.sources.crossref.httpx.Client", return_value=mock_client):
            papers = CrossrefSource().fetch_recent(["quantum computing"], max_results=10)

        assert len(papers) == 1
        p = papers[0]
        assert p.title == "Advances in Quantum Computing"
        assert p.source == "crossref"
        assert p.doi == "10.1234/test.2024.001"
        assert p.published_date == date(2024, 3, 15)
        assert p.journal_name == "Physical Review Letters"
        assert len(p.authors) == 2
        assert p.authors[0]["name"] == "Jane Doe"
        assert p.authors[0]["affiliation"] == "MIT"
        assert p.authors[1]["name"] == "John Smith"
        assert "Quantum Physics" in p.keywords
        # Abstract should have HTML/JATS tags stripped
        assert "<jats:" not in (p.abstract or "")
        assert "quantum" in (p.abstract or "").lower()

    def test_fetch_returns_empty_for_no_keywords(self):
        papers = CrossrefSource().fetch_recent([], max_results=10)
        assert papers == []

    def test_parse_date_with_partial_parts(self):
        from app.services.sources.crossref import _parse_date

        assert _parse_date([[2024, 3]]) == date(2024, 3, 1)
        assert _parse_date([[2024]]) == date(2024, 1, 1)
        assert _parse_date(None) is None
        assert _parse_date([]) is None

    def test_handles_missing_author_name_parts(self):
        item = dict(_CR_RESPONSE["message"]["items"][0])
        item["author"] = [{"given": "", "family": "OnlyFamily", "affiliation": []}]
        response = {"message": {"items": [item]}}

        mock_resp = MagicMock()
        mock_resp.json.return_value = response
        mock_resp.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp

        with patch("app.services.sources.crossref.httpx.Client", return_value=mock_client):
            papers = CrossrefSource().fetch_recent(["quantum"], max_results=5)

        assert papers[0].authors[0]["name"] == "OnlyFamily"
