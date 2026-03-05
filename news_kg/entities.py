from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import cache

import dspy

from news_kg.models import AnyArticle, ResolvedEntity
from news_kg.utils import extract_sentence_context, load_prompt
from news_kg.wikidata import search_wikidata

_ENTITY_LABELS = {
    "person": "A named individual person",
    "organisation": "A named company, institution, government body, or group",
    "location": "A named place, country, city, or geographical feature",
}


@cache
def _get_gliner():
    from gliner2 import GLiNER2

    return GLiNER2.from_pretrained("fastino/gliner2-large-v1")


class _CleanEntities(dspy.Signature):
    __doc__ = load_prompt("clean_entities.txt")

    text: str = dspy.InputField(desc="The source text")
    raw_people: list[str] = dspy.InputField(
        desc="Person entities extracted by NER model"
    )
    raw_organisations: list[str] = dspy.InputField(
        desc="Organisation entities extracted by NER model"
    )
    raw_locations: list[str] = dspy.InputField(
        desc="Location entities extracted by NER model"
    )

    people: list[str] = dspy.OutputField(
        desc="Cleaned, deduplicated person names in their fullest form"
    )
    organisations: list[str] = dspy.OutputField(
        desc="Cleaned, deduplicated organisation names"
    )
    locations: list[str] = dspy.OutputField(desc="Cleaned, deduplicated location names")


class _WikidataCandidate(dspy.Signature):
    __doc__ = load_prompt("wikidata_candidate.txt")

    entity_name: str = dspy.InputField(desc="The entity to resolve")
    context: str = dspy.InputField(
        desc="One or more sentences from the source text containing the entity, providing disambiguating context"
    )
    candidates: str = dspy.InputField(
        desc="Numbered list of Wikidata candidates, each with ID, label, description, and aliases"
    )
    is_match: bool = dspy.OutputField(
        desc="True if one of the candidates is a plausible match for the entity in context, False otherwise"
    )
    entity_num: int = dspy.OutputField(
        desc="The numeric part of the Wikidata entity ID of the best match (e.g. 76 for Q76). Ignored if is_match is False."
    )


def _format_candidates(candidates: list[dict]) -> str:
    lines = []
    for c in candidates:
        aliases = ", ".join(c["aliases"]) if c["aliases"] else "none"
        lines.append(
            f"[{c['id']}] {c['label']}\n"
            f"   Description: {c['description'] or 'N/A'}\n"
            f"   Aliases: {aliases}"
        )
    return "\n".join(lines)


class EntityEnricher(dspy.Module):
    """Extracts, cleans, and resolves named entities from an article to Wikidata Q-values."""

    def __init__(self, search_limit: int = 50, max_workers: int = 10):
        super().__init__()
        self.search_limit = search_limit
        self.max_workers = max_workers
        self.clean = dspy.Predict(_CleanEntities)

    def forward(self, article: AnyArticle) -> list[ResolvedEntity]:
        if article.entities is not None:
            return article.entities

        model = _get_gliner()
        raw = model.extract_entities(article.text, _ENTITY_LABELS, include_spans=True)
        entities = raw.get("entities", {})

        raw_people = [e["text"] for e in entities.get("person", [])]
        raw_organisations = [e["text"] for e in entities.get("organisation", [])]
        raw_locations = [e["text"] for e in entities.get("location", [])]

        cleaned = self.clean(
            text=article.text,
            raw_people=raw_people,
            raw_organisations=raw_organisations,
            raw_locations=raw_locations,
        )

        all_entities = list(
            dict.fromkeys(
                [
                    *(cleaned.people or []),
                    *(cleaned.organisations or []),
                    *(cleaned.locations or []),
                ]
            )
        )

        def resolve(name: str) -> ResolvedEntity:
            try:
                context = extract_sentence_context(article.text, name)
                if not context:
                    return ResolvedEntity(name=name, wikidata_id=None)
                candidates = search_wikidata(name, limit=self.search_limit)
                if not candidates:
                    return ResolvedEntity(name=name, wikidata_id=None)
                valid_ids = {c["id"] for c in candidates}
                choose = dspy.Predict(_WikidataCandidate)
                result = choose(
                    entity_name=name,
                    context=context,
                    candidates=_format_candidates(candidates),
                )
                if not result.is_match:
                    return ResolvedEntity(name=name, wikidata_id=None)
                q_id = f"Q{result.entity_num}"
                if q_id not in valid_ids:
                    return ResolvedEntity(name=name, wikidata_id=None)
                return ResolvedEntity(name=name, wikidata_id=q_id)
            except Exception:
                return ResolvedEntity(name=name, wikidata_id=None)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(resolve, name): name for name in all_entities}
            resolved_map: dict[str, ResolvedEntity] = {}
            for future in as_completed(futures):
                entity = future.result()
                resolved_map[entity.name] = entity

        resolved = [
            resolved_map[name]
            for name in all_entities
            if name in resolved_map and resolved_map[name].wikidata_id is not None
        ]
        return resolved
