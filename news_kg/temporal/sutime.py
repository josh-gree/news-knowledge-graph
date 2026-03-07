from __future__ import annotations

from sutime import SUTime

_instance: SUTime | None = None


def _get_sutime() -> SUTime:
    global _instance
    if _instance is None:
        _instance = SUTime(mark_time_ranges=True, include_range=True)
    return _instance


def tag(text: str, doc_date: str) -> list[dict]:
    if not text:
        return []
    st = _get_sutime()
    raw = st.parse(text, reference_date=doc_date)
    return [
        {
            "text": r["text"],
            "type": r["type"],
            "value": r.get("value", ""),
            "start": r["start"],
            "end": r["end"],
        }
        for r in raw
    ]
