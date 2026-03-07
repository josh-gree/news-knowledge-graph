from unittest.mock import MagicMock, patch

import pytest

from news_kg.temporal.sutime import tag


def _make_raw_span(text="yesterday", type_="DATE", value="2024-01-01", start=0, end=9):
    return {"text": text, "type": type_, "value": value, "start": start, "end": end}


@pytest.fixture(autouse=True)
def reset_sutime_singleton():
    import news_kg.temporal.sutime as mod

    original = mod._instance
    mod._instance = None
    yield
    mod._instance = original


def test_empty_input_returns_empty_list():
    result = tag("", "2024-01-01")
    assert result == []


def test_output_shape():
    mock_sutime = MagicMock()
    mock_sutime.parse.return_value = [_make_raw_span()]

    with patch("news_kg.temporal.sutime._get_sutime", return_value=mock_sutime):
        result = tag("Barack Obama visited London yesterday.", "2024-01-01")

    assert len(result) == 1
    span = result[0]
    assert set(span.keys()) == {"text", "type", "value", "start", "end"}


def test_doc_date_forwarded():
    mock_sutime = MagicMock()
    mock_sutime.parse.return_value = []

    with patch("news_kg.temporal.sutime._get_sutime", return_value=mock_sutime):
        tag("Some text.", "2023-06-15")

    mock_sutime.parse.assert_called_once_with("Some text.", reference_date="2023-06-15")


def test_span_values_mapped_correctly():
    mock_sutime = MagicMock()
    mock_sutime.parse.return_value = [
        _make_raw_span(
            text="last week", type_="DATE", value="2023-12-25", start=5, end=14
        )
    ]

    with patch("news_kg.temporal.sutime._get_sutime", return_value=mock_sutime):
        result = tag("It was last week.", "2024-01-01")

    assert result[0] == {
        "text": "last week",
        "type": "DATE",
        "value": "2023-12-25",
        "start": 5,
        "end": 14,
    }


def test_missing_value_defaults_to_empty_string():
    mock_sutime = MagicMock()
    mock_sutime.parse.return_value = [
        {"text": "now", "type": "TIME", "start": 0, "end": 3}
    ]

    with patch("news_kg.temporal.sutime._get_sutime", return_value=mock_sutime):
        result = tag("now", "2024-01-01")

    assert result[0]["value"] == ""


@pytest.mark.live
def test_live_tag_returns_spans():
    result = tag("Barack Obama visited London yesterday.", "2024-01-01")
    assert len(result) >= 1
    for span in result:
        assert set(span.keys()) == {"text", "type", "value", "start", "end"}
