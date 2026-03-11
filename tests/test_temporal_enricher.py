from unittest.mock import patch

import dspy
import pytest

from news_kg.models import Event, TemporalAnnotation
from news_kg.temporal.enricher import (
    TemporalEnricher,
    _ArticleEvent,
    _ExtractionResult,
    _TemporalExpression,
)

_LIVE_URL = "https://www.theguardian.com/world/2026/mar/04/israel-fresh-strikes-tehran-beirut-iran-targets-us-bases-gulf"


@pytest.fixture
def enricher():
    return TemporalEnricher()


@pytest.fixture
def article(make_article):
    return make_article(text="The summit took place last Tuesday. It ended yesterday.")


def _make_predict_result(article_event=None, expressions=None):
    result = _ExtractionResult(
        article_event=article_event,
        expressions=expressions or [],
    )
    return dspy.Prediction(result=result)


def test_returns_temporal_annotation(enricher, article):
    predict_result = _make_predict_result(
        article_event=_ArticleEvent(
            description="Summit took place", value="2024-01-01"
        ),
        expressions=[_TemporalExpression(text="last Tuesday", value="2023-12-26")],
    )
    with patch("news_kg.temporal.enricher.sutime.tag", return_value=[]):
        with patch("news_kg.temporal.enricher.heideltime.tag", return_value=[]):
            with patch.object(enricher, "predict", return_value=predict_result):
                result = enricher(article)

    assert isinstance(result, TemporalAnnotation)
    assert result.main_event == Event(text="Summit took place", value="2024-01-01")
    assert result.other_events == [Event(text="last Tuesday", value="2023-12-26")]


def test_short_circuits_if_already_enriched(enricher, make_article):
    existing = TemporalAnnotation(
        main_event=Event(text="Existing event", value="2024-01-01"),
    )
    article = make_article(temporal=existing)

    result = enricher(article)

    assert result is existing


def test_main_event_none_when_article_event_null(enricher, article):
    predict_result = _make_predict_result(
        article_event=None,
        expressions=[_TemporalExpression(text="yesterday", value="2023-12-31")],
    )
    with patch("news_kg.temporal.enricher.sutime.tag", return_value=[]):
        with patch("news_kg.temporal.enricher.heideltime.tag", return_value=[]):
            with patch.object(enricher, "predict", return_value=predict_result):
                result = enricher(article)

    assert result.main_event is None
    assert len(result.other_events) == 1


def test_other_events_populated(enricher, article):
    predict_result = _make_predict_result(
        article_event=None,
        expressions=[
            _TemporalExpression(text="last Tuesday", value="2023-12-26"),
            _TemporalExpression(text="next month", value="2024-02"),
            _TemporalExpression(text="three days", value="P3D"),
        ],
    )
    with patch("news_kg.temporal.enricher.sutime.tag", return_value=[]):
        with patch("news_kg.temporal.enricher.heideltime.tag", return_value=[]):
            with patch.object(enricher, "predict", return_value=predict_result):
                result = enricher(article)

    assert len(result.other_events) == 3
    assert result.other_events[0] == Event(text="last Tuesday", value="2023-12-26")
    assert result.other_events[1] == Event(text="next month", value="2024-02")
    assert result.other_events[2] == Event(text="three days", value="P3D")


@pytest.mark.live
def test_enrich_temporal_real_article():
    import dspy
    from dotenv import load_dotenv

    from news_kg.fetch.guardian import fetch_article

    load_dotenv()
    dspy.configure(lm=dspy.LM("anthropic/claude-haiku-4-5-20251001"))
    article = fetch_article(_LIVE_URL)
    enricher = TemporalEnricher()
    result = enricher(article)
    assert isinstance(result, TemporalAnnotation)
    assert result.main_event is not None
    assert isinstance(result.main_event.text, str) and result.main_event.text
