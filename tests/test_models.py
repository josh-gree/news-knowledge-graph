from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from news_kg.models import (
    Article,
    EntityAnnotation,
    Event,
    TemporalAnnotation,
    article_adapter,
)


def test_article_construction(make_article):
    article = make_article()
    assert article.text == "Some article text."
    assert article.date == datetime(2024, 1, 1, tzinfo=UTC)
    assert article.url == "https://example.com/article"
    assert article.temporal is None
    assert article.entities is None


def test_article_with_enrichments(make_article):
    article = make_article(
        temporal=TemporalAnnotation(),
        entities=EntityAnnotation(),
    )
    assert article.temporal is not None
    assert article.entities is not None


def test_article_is_frozen(make_article):
    article = make_article()
    with pytest.raises(ValidationError):
        article.text = "changed"


def test_temporal_annotation_is_frozen():
    annotation = TemporalAnnotation()
    with pytest.raises(ValidationError):
        annotation.x = 1  # type: ignore[attr-defined]


def test_entity_annotation_is_frozen():
    annotation = EntityAnnotation()
    with pytest.raises(ValidationError):
        annotation.x = 1  # type: ignore[attr-defined]


def test_article_dict_round_trip(make_article):
    article = make_article()
    restored = article_adapter.validate_python(article.model_dump())
    assert restored == article


def test_article_dict_round_trip_with_enrichments(make_article):
    article = make_article(
        temporal=TemporalAnnotation(),
        entities=EntityAnnotation(),
    )
    restored = article_adapter.validate_python(article.model_dump())
    assert restored == article


def test_article_missing_required_fields():
    with pytest.raises(ValidationError):
        Article(text="only text", url="https://example.com")  # missing date

    with pytest.raises(ValidationError):
        Article(  # missing text
            date=datetime(2024, 1, 1, tzinfo=UTC), url="https://example.com"
        )

    with pytest.raises(ValidationError):
        Article(text="only text", date=datetime(2024, 1, 1, tzinfo=UTC))  # missing url


def make_event(**kwargs):
    defaults = {
        "text": "the summit began",
        "value": "2024-01-01",
    }
    return Event(**{**defaults, **kwargs})


def test_event_is_frozen():
    event = make_event()
    with pytest.raises(ValidationError):
        event.text = "changed"  # type: ignore[misc]


def test_temporal_annotation_defaults():
    annotation = TemporalAnnotation()
    assert annotation.main_event is None
    assert annotation.other_events == []


def test_article_dict_round_trip_with_full_temporal(make_article):
    annotation = TemporalAnnotation(
        main_event=make_event(),
        other_events=[make_event(text="last Tuesday", value="2024-01-02")],
    )
    article = make_article(temporal=annotation, entities=EntityAnnotation())
    restored = article_adapter.validate_python(article.model_dump())
    assert restored == article
