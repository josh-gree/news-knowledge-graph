from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

AnchorType = Literal["absolute", "dct", "event"]
ExpressionType = Literal["DATE", "TIME"]
ResolutionType = Literal["arithmetic", "coreference", "unresolvable"] | None
StatusType = Literal["actual", "scheduled", "hypothetical"]


class Event(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    type: ExpressionType
    anchor: AnchorType
    anchor_event: str | None
    anchor_date: str | None
    value: str | None
    resolution: ResolutionType
    coreferent: str | None
    event: str
    status: StatusType


class MainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    description: str
    value: str


class TemporalAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True)

    main_event: MainEvent | None = None
    events: list[Event] = []


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
