from unittest.mock import patch

import pytest

from news_kg.temporal.heideltime import tag


def _make_raw_span(text="yesterday", type_="DATE", value="2024-01-01", start=0, end=9):
    return {"text": text, "type": type_, "value": value, "span": [start, end]}


def test_empty_input_returns_empty_list():
    result = tag("", "2024-01-01")
    assert result == []


def test_output_shape():
    with patch(
        "news_kg.temporal.heideltime.py_heideltime.heideltime",
        return_value=[_make_raw_span()],
    ):
        result = tag("Barack Obama visited London yesterday.", "2024-01-01")

    assert len(result) == 1
    span = result[0]
    assert set(span.keys()) == {"text", "type", "value", "start", "end"}


def test_doc_date_forwarded():
    with patch(
        "news_kg.temporal.heideltime.py_heideltime.heideltime", return_value=[]
    ) as mock_ht:
        tag("Some text.", "2023-06-15")

    mock_ht.assert_called_once_with(
        "Some text.", language="english", document_type="news", dct="2023-06-15"
    )


def test_span_values_mapped_correctly():
    with patch(
        "news_kg.temporal.heideltime.py_heideltime.heideltime",
        return_value=[
            _make_raw_span(
                text="last week", type_="DATE", value="2023-12-25", start=5, end=14
            )
        ],
    ):
        result = tag("It was last week.", "2024-01-01")

    assert result[0] == {
        "text": "last week",
        "type": "DATE",
        "value": "2023-12-25",
        "start": 5,
        "end": 14,
    }


def test_missing_value_defaults_to_empty_string():
    with patch(
        "news_kg.temporal.heideltime.py_heideltime.heideltime",
        return_value=[{"text": "now", "type": "TIME", "span": [0, 3]}],
    ):
        result = tag("now", "2024-01-01")

    assert result[0]["value"] == ""


@pytest.mark.live
def test_live_tag_returns_spans():
    result = tag("Barack Obama visited London yesterday.", "2024-01-01")
    assert len(result) >= 1
    for span in result:
        assert set(span.keys()) == {"text", "type", "value", "start", "end"}
