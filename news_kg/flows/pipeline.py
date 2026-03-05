import logging
from pathlib import Path

from prefect import flow, task

from news_kg.entities import EntityEnricher
from news_kg.fetch.guardian import _fetch_feed_urls
from news_kg.fetch.guardian import fetch_article as _fetch_article
from news_kg.models import AnyArticle
from news_kg.store import FilesystemStore

logger = logging.getLogger(__name__)


@task
def fetch_feed_task(feed_url: str) -> list[str]:
    return _fetch_feed_urls(feed_url)


@task
def fetch_article_task(url: str) -> AnyArticle:
    return _fetch_article(url)


@task
def enrich_entities_task(article: AnyArticle) -> AnyArticle:
    enricher = EntityEnricher()
    annotation = enricher(article)
    return article.model_copy(update={"entities": annotation})


@task
def save_article_task(article: AnyArticle, root: Path) -> str:
    return FilesystemStore(root).save(article)


@flow
def run_feed_pipeline(feed_url: str, root: Path) -> list[str]:
    urls = fetch_feed_task(feed_url)
    article_ids = []
    for url in urls:
        try:
            article = fetch_article_task(url)
        except Exception:
            logger.warning("Failed to fetch article, skipping: %s", url)
            continue
        enriched = enrich_entities_task(article)
        article_ids.append(save_article_task(enriched, root))
    return article_ids
