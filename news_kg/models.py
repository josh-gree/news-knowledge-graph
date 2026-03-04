from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TemporalAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True)


class EntityAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True)


class Article(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    date: datetime
    temporal: TemporalAnnotation | None = None
    entities: EntityAnnotation | None = None
