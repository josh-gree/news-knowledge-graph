from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Stub — fields to be added when temporal enrichment is implemented.
class TemporalAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True)


# Stub — fields to be added when entity enrichment is implemented.
class EntityAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True)


class Article(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    date: datetime
    url: str
    temporal: TemporalAnnotation | None = None
    entities: EntityAnnotation | None = None
