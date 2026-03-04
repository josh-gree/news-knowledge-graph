from datetime import UTC, datetime

import httpx
import pytest
import respx

from news_kg.fetch.guardian import _parse_doc_date, fetch_article
from news_kg.models import GuardianArticle

ARTICLE_URL = "https://www.theguardian.com/world/2024/jan/15/some-article-slug"

ARTICLE_HTML = """
<html>
<body>
  <div data-gu-name="headline">Test Headline</div>
  <div data-gu-name="standfirst">Test standfirst text</div>
  <div data-gu-name="byline">Jane Smith</div>
  <div data-gu-name="dateline">London</div>
  <div data-gu-name="body">
    <span data-print-layout="hide">Hidden text</span>
    Main body content here.
  </div>
</body>
</html>
"""


def test_parse_doc_date_standard_url():
    url = "https://www.theguardian.com/world/2024/jan/15/some-slug"
    assert _parse_doc_date(url) == datetime(2024, 1, 15, tzinfo=UTC)


def test_parse_doc_date_single_digit_day():
    url = "https://www.theguardian.com/world/2023/mar/5/some-slug"
    assert _parse_doc_date(url) == datetime(2023, 3, 5, tzinfo=UTC)


@pytest.mark.parametrize(
    "abbr,num",
    [
        ("jan", 1),
        ("feb", 2),
        ("mar", 3),
        ("apr", 4),
        ("may", 5),
        ("jun", 6),
        ("jul", 7),
        ("aug", 8),
        ("sep", 9),
        ("oct", 10),
        ("nov", 11),
        ("dec", 12),
    ],
)
def test_parse_doc_date_all_months(abbr, num):
    url = f"https://www.theguardian.com/uk/2024/{abbr}/10/slug"
    assert _parse_doc_date(url).month == num


def test_parse_doc_date_missing_date_raises():
    with pytest.raises(ValueError, match="Cannot extract date"):
        _parse_doc_date("https://www.theguardian.com/no-date-here")


@respx.mock
def test_fetch_article_returns_guardian_article():
    respx.get(ARTICLE_URL).mock(return_value=httpx.Response(200, text=ARTICLE_HTML))
    article = fetch_article(ARTICLE_URL)
    assert isinstance(article, GuardianArticle)
    assert article.url == ARTICLE_URL
    assert article.date == datetime(2024, 1, 15, tzinfo=UTC)
    assert article.headline == "Test Headline"
    assert article.standfirst == "Test standfirst text"
    assert article.byline == "Jane Smith"
    assert article.dateline == "London"
    assert "Main body content here." in article.text


@respx.mock
def test_fetch_article_text_is_body_only():
    respx.get(ARTICLE_URL).mock(return_value=httpx.Response(200, text=ARTICLE_HTML))
    article = fetch_article(ARTICLE_URL)
    assert "Test Headline" not in article.text
    assert "Test standfirst text" not in article.text


@respx.mock
def test_fetch_article_excludes_hidden_elements():
    respx.get(ARTICLE_URL).mock(return_value=httpx.Response(200, text=ARTICLE_HTML))
    article = fetch_article(ARTICLE_URL)
    assert "Hidden text" not in article.text


@respx.mock
def test_fetch_article_http_error_propagates():
    respx.get(ARTICLE_URL).mock(return_value=httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        fetch_article(ARTICLE_URL)


@pytest.mark.live
def test_fetch_article_real_guardian_article():
    url = "https://www.theguardian.com/world/2026/mar/04/israel-fresh-strikes-tehran-beirut-iran-targets-us-bases-gulf"
    article = fetch_article(url)
    assert isinstance(article, GuardianArticle)
    assert article.url == url
    assert article.date == datetime(2026, 3, 4, tzinfo=UTC)
    assert article.headline
    assert article.text
