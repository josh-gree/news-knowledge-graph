from datetime import UTC, datetime

import pytest

from news_kg.models import Article


@pytest.fixture
def make_article():
    def _make(**kwargs) -> Article:
        defaults = {
            "text": "Some article text.",
            "date": datetime(2024, 1, 1, tzinfo=UTC),
            "url": "https://example.com/article",
        }
        return Article(**{**defaults, **kwargs})

    return _make
