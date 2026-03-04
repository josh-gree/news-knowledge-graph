from datetime import UTC, datetime

import pytest

from news_kg.models import GuardianArticle


@pytest.fixture
def make_article():
    def _make(**kwargs) -> GuardianArticle:
        defaults = {
            "text": "Some article text.",
            "date": datetime(2024, 1, 1, tzinfo=UTC),
            "url": "https://example.com/article",
            "headline": "Some Headline",
            "standfirst": "Some standfirst.",
            "byline": "Some Author",
            "dateline": "London",
        }
        return GuardianArticle(**{**defaults, **kwargs})

    return _make
