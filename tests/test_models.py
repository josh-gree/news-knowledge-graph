from datetime import UTC, datetime

import pytest

from news_kg.models import Article, EntityAnnotation, TemporalAnnotation


def make_article(**kwargs):
    defaults = {
        "text": "Some article text.",
        "date": datetime(2024, 1, 1, tzinfo=UTC),
    }
    return Article(**{**defaults, **kwargs})


def test_article_construction():
    article = make_article()
    assert article.text == "Some article text."
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
    with pytest.raises(Exception):
        article.text = "changed"


def test_article_json_round_trip():
    article = make_article()
    restored = Article.model_validate(article.model_dump())
    assert restored == article


def test_article_json_round_trip_with_enrichments():
    article = make_article(
        temporal=TemporalAnnotation(),
        entities=EntityAnnotation(),
    )
    restored = Article.model_validate(article.model_dump())
    assert restored == article
