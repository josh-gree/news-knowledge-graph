import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from news_kg.models import Article, EntityAnnotation, TemporalAnnotation
from news_kg.store import FilesystemStore


def make_article(**kwargs) -> Article:
    defaults = {
        "text": "Some article text.",
        "date": datetime(2024, 1, 1, tzinfo=UTC),
        "url": "https://example.com/article",
    }
    return Article(**{**defaults, **kwargs})


def article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def test_store_creates_directory(tmp_path: Path) -> None:
    root = tmp_path / "store"
    assert not root.exists()
    FilesystemStore(root)
    assert root.exists()


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    store = FilesystemStore(tmp_path)
    article = make_article()
    aid = store.save(article)
    loaded = store.load(aid)
    assert loaded == article


def test_exists_before_and_after_save(tmp_path: Path) -> None:
    store = FilesystemStore(tmp_path)
    article = make_article()
    aid = article_id(article.url)
    assert not store.exists(aid)
    store.save(article)
    assert store.exists(aid)


def test_all_returns_all_articles(tmp_path: Path) -> None:
    store = FilesystemStore(tmp_path)
    articles = [
        make_article(url="https://example.com/1"),
        make_article(url="https://example.com/2"),
        make_article(url="https://example.com/3"),
    ]
    for a in articles:
        store.save(a)
    result = list(store.all())
    assert len(result) == 3
    assert set(a.url for a in result) == {
        "https://example.com/1",
        "https://example.com/2",
        "https://example.com/3",
    }


def test_load_missing_raises_key_error(tmp_path: Path) -> None:
    store = FilesystemStore(tmp_path)
    with pytest.raises(KeyError):
        store.load("nonexistent-id")


def test_save_merges_enrichments(tmp_path: Path) -> None:
    store = FilesystemStore(tmp_path)
    base = make_article()
    aid = store.save(base)

    enriched = make_article(
        temporal=TemporalAnnotation(),
        entities=EntityAnnotation(),
    )
    store.save(enriched)

    loaded = store.load(aid)
    assert loaded.text == base.text
    assert loaded.date == base.date
    assert loaded.url == base.url
    assert loaded.temporal is not None
    assert loaded.entities is not None


def test_save_merge_preserves_existing_enrichments(tmp_path: Path) -> None:
    store = FilesystemStore(tmp_path)
    first = make_article(temporal=TemporalAnnotation())
    aid = store.save(first)

    second = make_article(entities=EntityAnnotation())
    store.save(second)

    loaded = store.load(aid)
    assert loaded.temporal is not None
    assert loaded.entities is not None


def test_save_returns_article_id(tmp_path: Path) -> None:
    store = FilesystemStore(tmp_path)
    article = make_article()
    aid = store.save(article)
    assert aid == article_id(article.url)
