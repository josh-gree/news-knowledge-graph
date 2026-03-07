from __future__ import annotations

from pathlib import Path

from sutime import SUTime

_instance: SUTime | None = None

_JARS_DIR = Path(__file__).parents[2] / "jars"


def _get_sutime() -> SUTime:
    # Single-threaded use assumed; no locking around JVM initialisation.
    global _instance
    if _instance is None:
        _instance = SUTime(
            mark_time_ranges=True, include_range=True, jars=str(_JARS_DIR)
        )
    return _instance


def tag(text: str, doc_date: str) -> list[dict]:
    if not text:
        return []
    st = _get_sutime()
    raw = st.parse(text, reference_date=doc_date)
    return [
        {
            "text": r.get("text", ""),
            "type": r.get("type", ""),
            "value": r.get("value", ""),
            "start": r.get("start"),
            "end": r.get("end"),
        }
        for r in raw
    ]
