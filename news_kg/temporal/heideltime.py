from __future__ import annotations

import py_heideltime


def tag(text: str, doc_date: str) -> list[dict]:
    if not text:
        return []
    raw = py_heideltime.heideltime(
        text, language="english", document_type="news", dct=doc_date
    )
    return [
        {
            "text": r.get("text", ""),
            "type": r.get("type", ""),
            "value": r.get("value", ""),
            "start": r.get("span", [None])[0],
            "end": r.get("span", [None, None])[1],
        }
        for r in raw
    ]
