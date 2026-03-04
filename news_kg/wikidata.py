import httpx

_SEARCH_URL = "https://www.wikidata.org/w/api.php"
_HEADERS = {
    "User-Agent": "news-knowledge-graph/0.1 (https://github.com/josh-gree/news-knowledge-graph)"
}


def search_wikidata(query: str, limit: int = 50) -> list[dict]:
    """Search Wikidata for entities matching query.

    Returns a list of candidates, each with 'id' (Q-value), 'label', 'description', and 'aliases'.
    """
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "format": "json",
        "limit": limit,
    }
    response = httpx.get(_SEARCH_URL, params=params, headers=_HEADERS, timeout=10)
    response.raise_for_status()
    data = response.json()
    return [
        {
            "id": hit.get("id", ""),
            "label": hit.get("label", ""),
            "description": hit.get("description", ""),
            "aliases": hit.get("aliases", []),
        }
        for hit in data.get("search", [])
    ]
