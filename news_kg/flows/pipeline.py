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
def save_article_task(article: AnyArticle, store: FilesystemStore) -> str:
    return store.save(article)


@flow
def run_entity_pipeline(urls: list[str], store: FilesystemStore) -> list[str]:
    article_ids = []
    for url in urls:
        article = fetch_article_task(url)
        enriched = enrich_entities_task(article)
        article_id = save_article_task(enriched, store)
        article_ids.append(article_id)
    return article_ids
