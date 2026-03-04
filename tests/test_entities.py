from unittest.mock import MagicMock, patch

import dspy
import pytest

from news_kg.entities import EntityEnricher
from news_kg.fetch.guardian import fetch_article
from news_kg.models import EntityAnnotation, ResolvedEntity

_LIVE_URL = "https://www.theguardian.com/world/2026/mar/04/israel-fresh-strikes-tehran-beirut-iran-targets-us-bases-gulf"


@pytest.fixture
def enricher():
    return EntityEnricher()


@pytest.fixture
def article(make_article):
    return make_article(text="Barack Obama visited London. He met the Prime Minister.")


def _make_gliner_result(people=None, organisations=None, locations=None):
    return {
        "entities": {
            "person": [{"text": t, "start": 0, "end": len(t)} for t in (people or [])],
            "organisation": [
                {"text": t, "start": 0, "end": len(t)} for t in (organisations or [])
            ],
            "location": [
                {"text": t, "start": 0, "end": len(t)} for t in (locations or [])
            ],
        }
    }


def test_returns_entity_annotation(enricher, article):
    mock_gliner = MagicMock()
    mock_gliner.extract_entities.return_value = _make_gliner_result(
        people=["Barack Obama"], locations=["London"]
    )

    with patch("news_kg.entities._get_gliner", return_value=mock_gliner):
        with patch.object(enricher, "clean") as mock_clean:
            mock_clean.return_value = dspy.Prediction(
                people=["Barack Obama"], organisations=[], locations=["London"]
            )
            with patch.object(enricher, "choose") as mock_choose:
                mock_choose.return_value = dspy.Prediction(is_match=True, entity_num=76)
                with patch("news_kg.entities.search_wikidata") as mock_search:
                    mock_search.return_value = [
                        {
                            "id": "Q76",
                            "label": "Barack Obama",
                            "description": "",
                            "aliases": [],
                        }
                    ]
                    result = enricher(article)

    assert isinstance(result, EntityAnnotation)
    assert any(e.name == "Barack Obama" for e in result.entities)


def test_short_circuits_if_already_enriched(enricher, make_article):
    existing = EntityAnnotation(
        entities=[ResolvedEntity(name="Existing Entity", wikidata_id="Q1")]
    )
    article = make_article(entities=existing)

    result = enricher(article)

    assert result is existing


def test_wikidata_id_is_none_when_no_match(enricher, article):
    mock_gliner = MagicMock()
    mock_gliner.extract_entities.return_value = _make_gliner_result(
        people=["Barack Obama"]
    )

    with patch("news_kg.entities._get_gliner", return_value=mock_gliner):
        with patch.object(enricher, "clean") as mock_clean:
            mock_clean.return_value = dspy.Prediction(
                people=["Barack Obama"], organisations=[], locations=[]
            )
            with patch.object(enricher, "choose") as mock_choose:
                mock_choose.return_value = dspy.Prediction(is_match=False, entity_num=0)
                with patch("news_kg.entities.search_wikidata") as mock_search:
                    mock_search.return_value = [
                        {
                            "id": "Q76",
                            "label": "Barack Obama",
                            "description": "",
                            "aliases": [],
                        }
                    ]
                    result = enricher(article)

    assert result.entities[0].wikidata_id is None


def test_wikidata_id_is_none_when_no_candidates(enricher, article):
    mock_gliner = MagicMock()
    mock_gliner.extract_entities.return_value = _make_gliner_result(
        people=["Barack Obama"]
    )

    with patch("news_kg.entities._get_gliner", return_value=mock_gliner):
        with patch.object(enricher, "clean") as mock_clean:
            mock_clean.return_value = dspy.Prediction(
                people=["Barack Obama"], organisations=[], locations=[]
            )
            with patch("news_kg.entities.search_wikidata") as mock_search:
                mock_search.return_value = []
                result = enricher(article)

    assert result.entities[0].wikidata_id is None


@pytest.mark.live
def test_enrich_entities_real_article():
    import dspy
    from dotenv import load_dotenv

    load_dotenv()
    dspy.configure(lm=dspy.LM("anthropic/claude-haiku-4-5-20251001"))
    article = fetch_article(_LIVE_URL)
    enricher = EntityEnricher()
    result = enricher(article)
    assert isinstance(result, EntityAnnotation)
    assert len(result.entities) > 0
    assert all(isinstance(e.name, str) and e.name for e in result.entities)
