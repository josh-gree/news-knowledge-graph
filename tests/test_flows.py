from unittest.mock import MagicMock, patch

from news_kg.flows.pipeline import run_feed_pipeline
from news_kg.models import ResolvedEntity
from news_kg.store import FilesystemStore


def test_run_feed_pipeline_fetches_enriches_saves(make_article, tmp_path):
    feed_url = "https://www.theguardian.com/world/rss"
    url = "https://www.theguardian.com/world/2024/jan/01/test"
    article = make_article(url=url)
    annotation = [ResolvedEntity(name="London", wikidata_id="Q84")]
    mock_enricher_instance = MagicMock(return_value=annotation)

    with patch("news_kg.flows.pipeline._fetch_feed_urls", return_value=[url]):
        with patch("news_kg.flows.pipeline._fetch_article", return_value=article):
            with patch(
                "news_kg.flows.pipeline.EntityEnricher",
                return_value=mock_enricher_instance,
            ):
                result = run_feed_pipeline(feed_url, tmp_path)

    assert len(result) == 1
    saved = FilesystemStore(tmp_path).load(result[0])
    assert saved.entities == annotation


def test_run_feed_pipeline_processes_multiple_urls(make_article, tmp_path):
    feed_url = "https://www.theguardian.com/world/rss"
    urls = [
        "https://www.theguardian.com/world/2024/jan/01/first",
        "https://www.theguardian.com/world/2024/jan/02/second",
    ]
    articles = [make_article(url=url) for url in urls]
    annotation = []
    mock_enricher_instance = MagicMock(return_value=annotation)

    with patch("news_kg.flows.pipeline._fetch_feed_urls", return_value=urls):
        with patch("news_kg.flows.pipeline._fetch_article", side_effect=articles):
            with patch(
                "news_kg.flows.pipeline.EntityEnricher",
                return_value=mock_enricher_instance,
            ):
                result = run_feed_pipeline(feed_url, tmp_path)

    assert len(result) == 2


def test_run_feed_pipeline_empty_feed(tmp_path):
    with patch("news_kg.flows.pipeline._fetch_feed_urls", return_value=[]):
        result = run_feed_pipeline("https://www.theguardian.com/world/rss", tmp_path)

    assert result == []


def test_plain_functions_importable_without_prefect():
    from news_kg.entities import EntityEnricher
    from news_kg.fetch.guardian import fetch_article

    assert callable(fetch_article)
    assert callable(EntityEnricher)
