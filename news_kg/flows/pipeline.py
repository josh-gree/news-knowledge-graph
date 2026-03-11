import logging
from pathlib import Path

from prefect import flow, task

from news_kg.entities import EntityEnricher
from news_kg.fetch.guardian import fetch_feed
from news_kg.models import AnyArticle
from news_kg.store import FilesystemStore
from news_kg.temporal.enricher import TemporalEnricher

logger = logging.getLogger(__name__)


@task
def fetch_feed_task(feed_url: str, root: Path) -> list[AnyArticle]:
    return fetch_feed(feed_url, FilesystemStore(root))


@task
def enrich_entities_task(article: AnyArticle) -> AnyArticle:
    enricher = EntityEnricher()
    annotation = enricher(article)
    return article.model_copy(update={"entities": annotation})


@task
def enrich_temporal_task(article: AnyArticle) -> AnyArticle:
    enricher = TemporalEnricher()
    annotation = enricher(article)
    return article.model_copy(update={"temporal": annotation})


@task
def save_article_task(article: AnyArticle, root: Path) -> str:
    return FilesystemStore(root).save(article)


@flow
def run_feed_pipeline(feed_url: str, root: Path) -> list[str]:
    articles = fetch_feed_task(feed_url, root)
    article_ids = []
    for article in articles:
        try:
            enriched = enrich_entities_task(article)
            enriched = enrich_temporal_task(enriched)
        except Exception:
            logger.warning("Failed to enrich article, skipping: %s", article.url)
            continue
        article_ids.append(save_article_task(enriched, root))
    return article_ids
