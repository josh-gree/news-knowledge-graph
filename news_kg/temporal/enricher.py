from __future__ import annotations

import dspy
from pydantic import BaseModel

from news_kg.models import AnyArticle, Event, TemporalAnnotation
from news_kg.temporal import heideltime, sutime
from news_kg.utils import load_prompt


class _ArticleEvent(BaseModel):
    description: str
    value: str | None


class _TemporalExpression(BaseModel):
    text: str
    value: str | None


class _ExtractionResult(BaseModel):
    article_event: _ArticleEvent | None
    expressions: list[_TemporalExpression]


class _TemporalExtraction(dspy.Signature):
    __doc__ = load_prompt("temporal_enrichment.txt")

    doc_date: str = dspy.InputField(desc="Publication date of the article (YYYY-MM-DD)")
    article_text: str = dspy.InputField(desc="Full text of the news article")
    sutime_spans: list[dict] = dspy.InputField(desc="TIMEX3 spans extracted by SUTime")
    heideltime_spans: list[dict] = dspy.InputField(
        desc="TIMEX3 spans extracted by HeidelTime"
    )
    result: _ExtractionResult = dspy.OutputField(
        desc="Structured temporal annotation with main event and other expressions"
    )


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
            Event(text=expr.text, value=expr.value) for expr in result.expressions
        ]

        return TemporalAnnotation(main_event=main_event, other_events=other_events)
