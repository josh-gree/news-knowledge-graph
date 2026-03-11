from __future__ import annotations

from typing import Literal

import dspy
from pydantic import BaseModel

from news_kg.models import AnyArticle, Event, TemporalAnnotation
from news_kg.temporal import heideltime, sutime
from news_kg.utils import load_prompt

_AnchorType = Literal["absolute", "dct", "event"]
_ExpressionType = Literal["DATE", "TIME"]
_ResolutionType = Literal["arithmetic", "coreference", "unresolvable"] | None
_StatusType = Literal["actual", "scheduled", "hypothetical"]


class _TemporalExpression(BaseModel):
    text: str
    type: _ExpressionType
    anchor: _AnchorType
    anchor_event: str | None
    anchor_date: str | None
    value: str | None
    resolution: _ResolutionType
    coreferent: str | None
    event: str
    status: _StatusType


class _ArticleEvent(BaseModel):
    description: str
    value: str | None


class _ExtractionResult(BaseModel):
    doc_date: str
    article_event: _ArticleEvent | None
    expressions: list[_TemporalExpression]


class _TemporalExtraction(dspy.Signature):
    __doc__ = load_prompt("temporal_enrichment.txt")

    doc_date: str = dspy.InputField(desc="Document creation date (YYYY-MM-DD)")
    article_text: str = dspy.InputField(desc="Full article text (title + body)")
    sutime_spans: list[dict] = dspy.InputField(desc="SUTime TIMEX3 candidate spans")
    heideltime_spans: list[dict] = dspy.InputField(
        desc="HeidelTime TIMEX3 candidate spans"
    )
    result: _ExtractionResult = dspy.OutputField(desc="Extracted temporal expressions")


class TemporalEnricher(dspy.Module):
    """Reconciles SUTime and HeidelTime spans into a structured TemporalAnnotation."""

    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict(_TemporalExtraction)

    def forward(self, article: AnyArticle) -> TemporalAnnotation:
        if article.temporal is not None:
            return article.temporal

        doc_date = article.date.strftime("%Y-%m-%d")
        su_spans = sutime.tag(article.text, doc_date)
        ht_spans = heideltime.tag(article.text, doc_date)

        result: _ExtractionResult = self.predict(
            doc_date=doc_date,
            article_text=article.text,
            sutime_spans=su_spans,
            heideltime_spans=ht_spans,
        ).result

        main_event: Event | None = None
        if result.article_event is not None:
            main_event = Event(
                text=result.article_event.description,
                value=result.article_event.value,
            )

        other_events = [
            Event(text=expr.event, value=expr.value)
            for expr in result.expressions
            if expr.value is not None
        ]

        return TemporalAnnotation(main_event=main_event, other_events=other_events)
