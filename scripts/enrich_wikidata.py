"""Fetch one-hop Wikidata neighbourhood for each Entity in Neo4j and add it to the graph."""

import time

import httpx
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "password")

API_URL = "https://www.wikidata.org/w/api.php"


def get_entity_ids(driver) -> list[str]:
    with driver.session() as session:
        result = session.run("MATCH (e:Entity) RETURN e.wikidata_id AS qid")
        return [r["qid"] for r in result]


def fetch_item_claims(qid: str, client: httpx.Client) -> list[tuple[str, str]]:
    """Return list of (property_id, target_qid) for all item-valued claims."""
    resp = client.get(
        API_URL,
        params={
            "action": "wbgetentities",
            "ids": qid,
            "props": "claims",
            "format": "json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    entity = data["entities"].get(qid) or next(iter(data["entities"].values()))
    claims = entity.get("claims", {})

    results = []
    for prop_id, statements in claims.items():
        for stmt in statements:
            snak = stmt.get("mainsnak", {})
            if snak.get("snaktype") != "value":
                continue
            if snak.get("datatype") != "wikibase-item":
                continue
            target_qid = snak["datavalue"]["value"].get("id")
            if target_qid:
                results.append((prop_id, target_qid))
    return results


def fetch_property_labels(prop_ids: list[str], client: httpx.Client) -> dict[str, str]:
    """Batch-fetch English labels for a list of property IDs."""
    labels = {}
    # API accepts max ~50 ids at a time
    total = -(-len(prop_ids) // 50)
    for batch_num, i in enumerate(range(0, len(prop_ids), 50), 1):
        print(f"    property labels batch {batch_num}/{total}")
        batch = prop_ids[i : i + 50]
        resp = client.get(
            API_URL,
            params={
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "labels",
                "languages": "en",
                "format": "json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        for pid, entity in data.get("entities", {}).items():
            label = entity.get("labels", {}).get("en", {}).get("value", pid)
            labels[pid] = label
        time.sleep(0.5)
    return labels


def fetch_entity_labels(qids: list[str], client: httpx.Client) -> dict[str, str]:
    """Batch-fetch English labels for a list of Q-ids."""
    labels = {}
    total = -(-len(qids) // 50)
    for batch_num, i in enumerate(range(0, len(qids), 50), 1):
        print(f"    entity labels batch {batch_num}/{total}")
        batch = qids[i : i + 50]
        resp = client.get(
            API_URL,
            params={
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "labels",
                "languages": "en",
                "format": "json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        for qid, entity in data.get("entities", {}).items():
            label = entity.get("labels", {}).get("en", {}).get("value", qid)
            labels[qid] = label
        time.sleep(0.5)
    return labels


def write_neighbourhood(
    driver,
    source_qid: str,
    claims: list[tuple[str, str]],
    prop_labels: dict[str, str],
    entity_labels: dict[str, str],
) -> None:
    with driver.session() as session:
        session.execute_write(_write, source_qid, claims, prop_labels, entity_labels)


def _write(tx, source_qid, claims, prop_labels, entity_labels):
    for prop_id, target_qid in claims:
        tx.run(
            """
            MERGE (target:Entity {wikidata_id: $target_qid})
            ON CREATE SET target.name = $target_label
            WITH target
            MATCH (source:Entity {wikidata_id: $source_qid})
            MERGE (source)-[r:WD_CLAIM {property_id: $prop_id}]->(target)
            SET r.property_label = $prop_label
            """,
            source_qid=source_qid,
            target_qid=target_qid,
            target_label=entity_labels.get(target_qid, target_qid),
            prop_id=prop_id,
            prop_label=prop_labels.get(prop_id, prop_id),
        )


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    try:
        qids = get_entity_ids(driver)
        print(f"Found {len(qids)} entities in graph")

        all_claims: dict[str, list[tuple[str, str]]] = {}
        all_prop_ids: set[str] = set()
        all_target_qids: set[str] = set()

        with httpx.Client(
            headers={
                "User-Agent": "news-knowledge-graph/0.1 (https://github.com/josh-gree/news-knowledge-graph)"
            }
        ) as client:
            for i, qid in enumerate(qids, 1):
                print(f"  [{i}/{len(qids)}] Fetching claims for {qid}...")
                claims = fetch_item_claims(qid, client)
                all_claims[qid] = claims
                for prop_id, target_qid in claims:
                    all_prop_ids.add(prop_id)
                    all_target_qids.add(target_qid)
                print(f"         -> {len(claims)} item-valued claims")
                time.sleep(0.5)

            n_prop_batches = -(-len(all_prop_ids) // 50)
            print(
                f"\nFetching labels for {len(all_prop_ids)} properties ({n_prop_batches} batches)..."
            )
            prop_labels = fetch_property_labels(list(all_prop_ids), client)

            n_entity_batches = -(-len(all_target_qids) // 50)
            print(
                f"Fetching labels for {len(all_target_qids)} target entities ({n_entity_batches} batches)..."
            )
            entity_labels = fetch_entity_labels(list(all_target_qids), client)

        print("\nWriting to Neo4j...")
        for i, (qid, claims) in enumerate(all_claims.items(), 1):
            write_neighbourhood(driver, qid, claims, prop_labels, entity_labels)
            print(f"  [{i}/{len(all_claims)}] Wrote {len(claims)} claims for {qid}")

        print("Done.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
