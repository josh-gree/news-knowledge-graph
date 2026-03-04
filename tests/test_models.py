from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from news_kg.models import Article, EntityAnnotation, TemporalAnnotation


def make_article(**kwargs):
    defaults = {
        "text": "Some article text.",
        "date": datetime(2024, 1, 1, tzinfo=UTC),
        "url": "https://example.com/article",
    }
    return Article(**{**defaults, **kwargs})


def test_article_construction():
    article = make_article()
    assert article.text == "Some article text."
    assert article.date == datetime(2024, 1, 1, tzinfo=UTC)
    assert article.url == "https://example.com/article"
    assert article.temporal is None
    assert article.entities is None


def test_article_with_enrichments():
    article = make_article(
        temporal=TemporalAnnotation(),
        entities=EntityAnnotation(),
    )
    assert article.temporal is not None
    assert article.entities is not None


def test_article_is_frozen():
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


def test_article_dict_round_trip():
    article = make_article()
    restored = Article.model_validate(article.model_dump())
    assert restored == article


def test_article_dict_round_trip_with_enrichments():
    article = make_article(
        temporal=TemporalAnnotation(),
        entities=EntityAnnotation(),
    )
    restored = Article.model_validate(article.model_dump())
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
