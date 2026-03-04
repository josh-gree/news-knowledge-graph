import re
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup

from news_kg.models import GuardianArticle

_DATE_RE = re.compile(r"/(\d{4})/([a-z]{3})/(\d{1,2})/")
_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _parse_doc_date(url: str) -> datetime:
    m = _DATE_RE.search(url)
    if not m:
        raise ValueError(f"Cannot extract date from URL: {url}")
    year, mon_str, day = int(m.group(1)), m.group(2), int(m.group(3))
    month = _MONTHS.get(mon_str)
    if month is None:
        raise ValueError(f"Unknown month abbreviation: {mon_str}")
    return datetime(year, month, day, tzinfo=UTC)


def _scrape(url: str) -> dict:
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    def extract(name: str) -> str:
        el = soup.find(attrs={"data-gu-name": name})
        if not el:
            return ""
        for hidden in el.find_all(attrs={"data-print-layout": "hide"}):
            hidden.decompose()
        return el.get_text(separator=" ", strip=True)

    return {
        "headline": extract("headline"),
        "standfirst": extract("standfirst"),
        "byline": extract("byline"),
        "dateline": extract("dateline"),
        "body": extract("body"),
    }


def fetch_article(url: str) -> GuardianArticle:
    date = _parse_doc_date(url)
    scraped = _scrape(url)
    return GuardianArticle(
        text=scraped["body"],
        date=date,
        url=url,
        headline=scraped["headline"],
        standfirst=scraped["standfirst"],
        byline=scraped["byline"],
        dateline=scraped["dateline"],
    )
