import pytest
import respx
from httpx import Response

from news_kg.wikidata import search_wikidata

_SEARCH_URL = "https://www.wikidata.org/w/api.php"


@respx.mock
def test_returns_candidates():
    respx.get(_SEARCH_URL).mock(
        return_value=Response(
            200,
            json={
                "search": [
                    {
                        "id": "Q76",
                        "label": "Barack Obama",
                        "description": "44th president of the United States",
                        "aliases": ["Obama"],
                    },
                    {
                        "id": "Q1234",
                        "label": "Barack Obama Sr.",
                        "description": "Kenyan economist",
                        "aliases": [],
                    },
                ]
            },
        )
    )

    results = search_wikidata("Barack Obama")

    assert len(results) == 2
    assert results[0]["id"] == "Q76"
    assert results[0]["label"] == "Barack Obama"
    assert results[0]["description"] == "44th president of the United States"
    assert results[0]["aliases"] == ["Obama"]


@respx.mock
def test_returns_empty_list_when_no_results():
    respx.get(_SEARCH_URL).mock(return_value=Response(200, json={"search": []}))

    results = search_wikidata("xyzzy nonexistent entity")

    assert results == []


@respx.mock
def test_passes_limit_param():
    request = respx.get(_SEARCH_URL).mock(
        return_value=Response(200, json={"search": []})
    )

    search_wikidata("test", limit=25)

    assert request.called
    assert "25" in str(request.calls[0].request.url)


@respx.mock
def test_raises_on_http_error():
    respx.get(_SEARCH_URL).mock(return_value=Response(500))

    with pytest.raises(Exception):
        search_wikidata("Barack Obama")
