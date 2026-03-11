from unittest.mock import MagicMock, patch

from news_kg.flows.pipeline import run_feed_pipeline
from news_kg.models import Event, ResolvedEntity, TemporalAnnotation
from news_kg.store import FilesystemStore


def test_run_feed_pipeline_fetches_enriches_saves(make_article, tmp_path):
    feed_url = "https://www.theguardian.com/world/rss"
    article = make_article()
    entity_annotation = [ResolvedEntity(name="London", wikidata_id="Q84")]
    temporal_annotation = TemporalAnnotation(
        main_event=Event(text="test event", value="2024-01-01"),
        other_events=[],
    )
    mock_entity_enricher = MagicMock(return_value=entity_annotation)
    mock_temporal_enricher = MagicMock(return_value=temporal_annotation)

    with patch("news_kg.flows.pipeline.fetch_feed", return_value=[article]):
        with patch(
            "news_kg.flows.pipeline.EntityEnricher",
            return_value=mock_entity_enricher,
        ):
            with patch(
                "news_kg.flows.pipeline.TemporalEnricher",
                return_value=mock_temporal_enricher,
            ):
                result = run_feed_pipeline(feed_url, tmp_path)

    assert len(result) == 1
    saved = FilesystemStore(tmp_path).load(result[0])
    assert saved.entities == entity_annotation
    assert saved.temporal == temporal_annotation


def test_run_feed_pipeline_processes_multiple_articles(make_article, tmp_path):
    feed_url = "https://www.theguardian.com/world/rss"
    articles = [
        make_article(url="https://www.theguardian.com/world/2024/jan/01/first"),
        make_article(url="https://www.theguardian.com/world/2024/jan/02/second"),
    ]
    mock_entity_enricher = MagicMock(return_value=[])
    mock_temporal_enricher = MagicMock(
        return_value=TemporalAnnotation(
            main_event=Event(text="event", value="2024-01-01"),
            other_events=[],
        )
    )

    with patch("news_kg.flows.pipeline.fetch_feed", return_value=articles):
        with patch(
            "news_kg.flows.pipeline.EntityEnricher",
            return_value=mock_entity_enricher,
        ):
            with patch(
                "news_kg.flows.pipeline.TemporalEnricher",
                return_value=mock_temporal_enricher,
            ):
                result = run_feed_pipeline(feed_url, tmp_path)

    assert len(result) == 2


def test_run_feed_pipeline_empty_feed(tmp_path):
    with patch("news_kg.flows.pipeline.fetch_feed", return_value=[]):
        result = run_feed_pipeline("https://www.theguardian.com/world/rss", tmp_path)

    assert result == []


def test_run_feed_pipeline_skips_article_on_enrichment_failure(make_article, tmp_path):
    feed_url = "https://www.theguardian.com/world/rss"
    articles = [
        make_article(url="https://www.theguardian.com/world/2024/jan/01/first"),
        make_article(url="https://www.theguardian.com/world/2024/jan/02/second"),
    ]
    mock_entity_enricher = MagicMock(side_effect=[Exception("enrichment failed"), []])
    mock_temporal_enricher = MagicMock(
        return_value=TemporalAnnotation(
            main_event=Event(text="event", value="2024-01-01"),
            other_events=[],
        )
    )

    with patch("news_kg.flows.pipeline.fetch_feed", return_value=articles):
        with patch(
            "news_kg.flows.pipeline.EntityEnricher",
            return_value=mock_entity_enricher,
        ):
            with patch(
                "news_kg.flows.pipeline.TemporalEnricher",
                return_value=mock_temporal_enricher,
            ):
                result = run_feed_pipeline(feed_url, tmp_path)

    assert len(result) == 1


def test_plain_functions_importable_without_prefect():
    from news_kg.entities import EntityEnricher
    from news_kg.fetch.guardian import fetch_feed
    from news_kg.temporal.enricher import TemporalEnricher

    assert callable(fetch_feed)
    assert callable(EntityEnricher)
    assert callable(TemporalEnricher)
