"""Quick-and-dirty ingestion of articles from FilesystemStore into Neo4j."""

from pathlib import Path

from neo4j import GraphDatabase

from news_kg.store import FilesystemStore

STORE_PATH = Path(__file__).parent / "store"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


def ingest(store: FilesystemStore, driver) -> None:
    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT article_url IF NOT EXISTS FOR (a:Article) REQUIRE a.url IS UNIQUE"
        )
        session.run(
            "CREATE CONSTRAINT entity_wikidata_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.wikidata_id IS UNIQUE"
        )

        for article in store.all():
            session.execute_write(_write_article, article)
            print(f"Ingested: {article.headline}")


def _write_article(tx, article) -> None:
    tx.run(
        """
        MERGE (a:Article {url: $url})
        SET a.headline   = $headline,
            a.date       = $date,
            a.source     = $source,
            a.byline     = $byline,
            a.standfirst = $standfirst,
            a.text       = $text
        """,
        url=article.url,
        headline=article.headline,
        date=article.date.isoformat(),
        source=article.source,
        byline=article.byline,
        standfirst=article.standfirst,
        text=article.text,
    )

    if article.entities:
        for entity in article.entities.entities:
            if not entity.wikidata_id:
                continue
            tx.run(
                """
                MERGE (e:Entity {wikidata_id: $wikidata_id})
                SET e.name = $name
                WITH e
                MATCH (a:Article {url: $url})
                MERGE (a)-[:MENTIONS]->(e)
                """,
                wikidata_id=entity.wikidata_id,
                name=entity.name,
                url=article.url,
            )


if __name__ == "__main__":
    store = FilesystemStore(STORE_PATH)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        ingest(store, driver)
        print("Done.")
    finally:
        driver.close()
