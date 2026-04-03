"""Tests for the RelevanceRanker scoring logic."""
from __future__ import annotations

import pytest

from app.services.ranking import RelevanceRanker
from app.services.sources.base import RawPaper


def _make_paper(**kwargs) -> RawPaper:
    defaults = dict(
        title="A Study on Machine Learning Techniques",
        source="arxiv",
        source_id="2401.00001",
        url="https://arxiv.org/abs/2401.00001",
        authors=[{"name": "John Doe", "affiliation": None}],
        abstract="This paper explores neural networks and deep learning methods.",
        journal_name=None,
    )
    defaults.update(kwargs)
    return RawPaper(**defaults)


def _make_prefs(**kwargs):
    """Return a simple namespace mimicking UserPreference."""
    from types import SimpleNamespace

    defaults = dict(
        keywords=[],
        exclude_keywords=[],
        follow_authors=[],
        preferred_sources=["arxiv", "openalex", "crossref"],
        preferred_journals=[],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


ranker = RelevanceRanker()


class TestKeywordScoring:
    def test_keyword_in_title_scores_10(self):
        paper = _make_paper(title="Machine Learning for NLP")
        prefs = _make_prefs(keywords=["machine learning"], preferred_sources=[])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert score == 10.0
        assert "machine learning" in breakdown["keyword_title_hits"]

    def test_keyword_in_abstract_scores_5(self):
        paper = _make_paper(title="Irrelevant Title", abstract="We use machine learning here.")
        prefs = _make_prefs(keywords=["machine learning"], preferred_sources=[])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert score == 5.0
        assert "machine learning" in breakdown["keyword_abstract_hits"]

    def test_keyword_title_takes_priority_over_abstract(self):
        paper = _make_paper(
            title="Machine Learning overview",
            abstract="machine learning is discussed",
        )
        prefs = _make_prefs(keywords=["machine learning"], preferred_sources=[])
        score, breakdown = ranker.score_paper(paper, prefs)
        # Title match (+10), abstract match ignored since title already matched
        assert score == 10.0
        assert "machine learning" in breakdown["keyword_title_hits"]
        assert "machine learning" not in breakdown["keyword_abstract_hits"]

    def test_multiple_keywords_accumulate(self):
        paper = _make_paper(
            title="Neural Networks and Deep Learning",
            abstract="We study transformers.",
        )
        prefs = _make_prefs(
            keywords=["neural networks", "deep learning", "transformers"],
            preferred_sources=[],
        )
        score, breakdown = ranker.score_paper(paper, prefs)
        # neural networks in title (+10), deep learning in title (+10), transformers in abstract (+5)
        assert score == 25.0

    def test_no_keywords_scores_zero_for_keywords(self):
        paper = _make_paper()
        prefs = _make_prefs(keywords=[])
        score, _ = ranker.score_paper(paper, prefs)
        # only source bonus applies
        assert score == 5.0  # preferred_sources includes arxiv


class TestExcludeKeywords:
    def test_exclude_keyword_in_title_penalises(self):
        paper = _make_paper(title="Spam Detection Survey")
        prefs = _make_prefs(keywords=[], exclude_keywords=["spam"])
        score, breakdown = ranker.score_paper(paper, prefs)
        # -20 from title, floored to 0 (source bonus +5 = -15 raw -> clamped 0)
        assert score == 0.0
        assert "spam" in breakdown["exclude_keyword_hits"]

    def test_exclude_keyword_in_abstract_penalises(self):
        paper = _make_paper(title="Normal Title", abstract="This is spam content.")
        prefs = _make_prefs(keywords=[], exclude_keywords=["spam"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert score == 0.0
        assert "spam" in breakdown["exclude_keyword_hits"]

    def test_exclude_keyword_does_not_trigger_on_miss(self):
        paper = _make_paper(title="Clean Research Paper")
        prefs = _make_prefs(keywords=[], exclude_keywords=["spam"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert "spam" not in breakdown["exclude_keyword_hits"]

    def test_exclude_penalty_applied_before_floor(self):
        paper = _make_paper(
            title="Machine Learning Spam Paper",
            abstract="neural networks and advertisement topics",
        )
        prefs = _make_prefs(
            keywords=["machine learning"],
            exclude_keywords=["spam", "advertisement"],
        )
        score, breakdown = ranker.score_paper(paper, prefs)
        # +10 (ml in title) -20 (spam in title) -20 (advertisement in abstract) +5 (source) = -25 raw -> 0
        assert score == 0.0
        assert breakdown["raw_score"] == -25.0


class TestAuthorScoring:
    def test_followed_author_match_boosts(self):
        paper = _make_paper(
            authors=[{"name": "Yann LeCun", "affiliation": "NYU"}]
        )
        prefs = _make_prefs(follow_authors=["Yann LeCun"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert score >= 15.0
        assert "Yann LeCun" in breakdown["author_hits"]

    def test_unmatched_author_no_boost(self):
        paper = _make_paper(authors=[{"name": "John Smith", "affiliation": None}])
        prefs = _make_prefs(follow_authors=["Yann LeCun"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert "Yann LeCun" not in breakdown["author_hits"]

    def test_partial_author_name_match(self):
        paper = _make_paper(authors=[{"name": "Geoffrey E. Hinton", "affiliation": None}])
        prefs = _make_prefs(follow_authors=["hinton"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert "hinton" in breakdown["author_hits"]


class TestPreferredSource:
    def test_preferred_source_gives_bonus(self):
        paper = _make_paper(source="arxiv")
        prefs = _make_prefs(preferred_sources=["arxiv"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert breakdown["source_bonus"] == 5.0

    def test_non_preferred_source_no_bonus(self):
        paper = _make_paper(source="crossref")
        prefs = _make_prefs(preferred_sources=["arxiv"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert breakdown["source_bonus"] == 0.0


class TestPreferredJournal:
    def test_preferred_journal_match_boosts(self):
        paper = _make_paper(journal_name="Nature Communications")
        prefs = _make_prefs(preferred_journals=["nature"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert "nature" in breakdown["journal_hits"]
        assert score >= 10.0

    def test_unmatched_journal_no_boost(self):
        paper = _make_paper(journal_name="Unknown Journal")
        prefs = _make_prefs(preferred_journals=["nature"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert "nature" not in breakdown["journal_hits"]


class TestScoreBreakdown:
    def test_breakdown_contains_all_keys(self):
        paper = _make_paper()
        prefs = _make_prefs()
        _, breakdown = ranker.score_paper(paper, prefs)
        for key in (
            "keyword_title_hits",
            "keyword_abstract_hits",
            "exclude_keyword_hits",
            "author_hits",
            "source_bonus",
            "journal_hits",
            "raw_score",
            "total_score",
        ):
            assert key in breakdown, f"Missing key: {key}"

    def test_total_score_matches_raw_score_when_positive(self):
        paper = _make_paper(title="Neural Networks Research")
        prefs = _make_prefs(keywords=["neural networks"])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert score == breakdown["total_score"]
        assert breakdown["total_score"] >= 0.0

    def test_score_is_floored_at_zero(self):
        paper = _make_paper(title="Spam Content Advertisement")
        prefs = _make_prefs(exclude_keywords=["spam", "advertisement"], preferred_sources=[])
        score, breakdown = ranker.score_paper(paper, prefs)
        assert score == 0.0
        assert breakdown["raw_score"] < 0
