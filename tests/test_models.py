from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from news_kg.models import (
    Article,
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
        entities=[],
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


def test_article_dict_round_trip(make_article):
    article = make_article()
    restored = article_adapter.validate_python(article.model_dump())
    assert restored == article


def test_article_dict_round_trip_with_enrichments(make_article):
    article = make_article(
        temporal=TemporalAnnotation(),
        entities=[],
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
