from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


# Stub — fields to be added when temporal enrichment is implemented.
class TemporalAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True)


class ResolvedEntity(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    wikidata_id: str | None = None


class EntityAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True)

    entities: list[ResolvedEntity] = []


class Article(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    date: datetime
    url: str
    temporal: TemporalAnnotation | None = None
    entities: EntityAnnotation | None = None


class GuardianArticle(Article):
    source: Literal["guardian"] = "guardian"
    headline: str = Field(min_length=1)
    standfirst: str = Field(min_length=1)
    byline: str = Field(min_length=1)
    dateline: str = Field(min_length=1)


# Union will grow as sources are added; `source` discriminator enables round-tripping.
AnyArticle = Annotated[GuardianArticle, Field(discriminator="source")]
article_adapter = TypeAdapter(AnyArticle)
