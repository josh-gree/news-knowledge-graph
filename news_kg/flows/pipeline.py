from pathlib import Path

from prefect import flow, task

from news_kg.entities import EntityEnricher
from news_kg.fetch.guardian import fetch_article as _fetch_article
from news_kg.models import AnyArticle
from news_kg.store import FilesystemStore


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
def run_entity_pipeline(urls: list[str], root: Path) -> list[str]:
    fetch_futures = [fetch_article_task.submit(url) for url in urls]
    enrich_futures = [enrich_entities_task.submit(f) for f in fetch_futures]
    save_futures = [save_article_task.submit(e, root) for e in enrich_futures]
    return [f.result() for f in save_futures]
