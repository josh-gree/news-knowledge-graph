from pathlib import Path

import pytest

from news_kg.models import EntityAnnotation, TemporalAnnotation
from news_kg.store import FilesystemStore, _article_id


def test_store_creates_directory(tmp_path: Path) -> None:
    root = tmp_path / "store"
    assert not root.exists()
    FilesystemStore(root)
    assert (root / "articles").exists()


def test_save_and_load_round_trip(tmp_path: Path, make_article) -> None:
    store = FilesystemStore(tmp_path)
    article = make_article()
    aid = store.save(article)
    loaded = store.load(aid)
    assert loaded == article


def test_exists_before_and_after_save(tmp_path: Path, make_article) -> None:
    store = FilesystemStore(tmp_path)
    article = make_article()
    aid = _article_id(article.url)
    assert not store.exists(aid)
    store.save(article)
    assert store.exists(aid)


def test_all_returns_all_articles(tmp_path: Path, make_article) -> None:
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


def test_save_overwrites_existing(tmp_path: Path, make_article) -> None:
    store = FilesystemStore(tmp_path)
    original = make_article()
    aid = store.save(original)

    updated = make_article(temporal=TemporalAnnotation(), entities=EntityAnnotation())
    store.save(updated)

    loaded = store.load(aid)
    assert loaded == updated


def test_save_returns_article_id(tmp_path: Path, make_article) -> None:
    store = FilesystemStore(tmp_path)
    article = make_article()
    aid = store.save(article)
    assert aid == _article_id(article.url)
