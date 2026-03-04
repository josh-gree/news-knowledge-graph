from unittest.mock import MagicMock, patch

from news_kg.flows.pipeline import run_entity_pipeline
from news_kg.models import EntityAnnotation, ResolvedEntity
from news_kg.store import FilesystemStore


def test_run_entity_pipeline_fetches_enriches_saves(make_article, tmp_path):
    url = "https://www.theguardian.com/2024/jan/01/test"
    article = make_article(url=url)
    annotation = EntityAnnotation(
        entities=[ResolvedEntity(name="London", wikidata_id="Q84")]
    )

    mock_enricher_instance = MagicMock(return_value=annotation)

    with patch("news_kg.flows.pipeline._fetch_article", return_value=article):
        with patch(
            "news_kg.flows.pipeline.EntityEnricher",
            return_value=mock_enricher_instance,
        ):
            result = run_entity_pipeline([url], tmp_path)

    assert len(result) == 1
    saved = FilesystemStore(tmp_path).load(result[0])
    assert saved.entities == annotation


def test_run_entity_pipeline_processes_multiple_urls(make_article, tmp_path):
    urls = [
        "https://www.theguardian.com/2024/jan/01/first",
        "https://www.theguardian.com/2024/jan/02/second",
    ]
    articles = [make_article(url=url) for url in urls]
    annotation = EntityAnnotation(entities=[])

    mock_enricher_instance = MagicMock(return_value=annotation)

    with patch("news_kg.flows.pipeline._fetch_article", side_effect=articles):
        with patch(
            "news_kg.flows.pipeline.EntityEnricher",
            return_value=mock_enricher_instance,
        ):
            result = run_entity_pipeline(urls, tmp_path)

    assert len(result) == 2


def test_plain_functions_importable_without_prefect():
    from news_kg.entities import EntityEnricher
    from news_kg.fetch.guardian import fetch_article

    assert callable(fetch_article)
    assert callable(EntityEnricher)
