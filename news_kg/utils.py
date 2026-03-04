import re
from importlib.resources import files


def load_prompt(name: str) -> str:
    return files("news_kg.prompts").joinpath(name).read_text(encoding="utf-8")


_SKIP_WORDS = {
    "a",
    "an",
    "the",
    "of",
    "in",
    "on",
    "at",
    "to",
    "for",
    "with",
    "by",
    "from",
    "into",
    "about",
    "as",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "out",
    "off",
    "over",
    "under",
    "and",
    "or",
    "but",
    "nor",
}


def _search_words(entity_text: str) -> list[str]:
    """Return the terms to search for a given entity string.

    For single-word entities returns just that word. For multi-word entities
    returns the full phrase plus each constituent word that is not a stop word.
    """
    words = entity_text.split()
    if len(words) == 1:
        return [entity_text]
    content_words = [w for w in words if w.lower() not in _SKIP_WORDS]
    return [entity_text] + content_words


def _split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Split text into sentences, returning (start, end, sentence) tuples."""
    sentences = []
    for m in re.finditer(r"[^.!?]+[.!?]?", text):
        sentence = m.group().strip()
        if sentence:
            sentences.append((m.start(), m.end(), sentence))
    return sentences


def extract_sentence_context(text: str, mention: str) -> str:
    """Return all sentences from text that contain any mention of the entity.

    Handles partial names: for 'Donald Trump', also searches for 'Donald' and 'Trump'.
    """
    sentences = _split_sentences(text)
    matched: dict[int, str] = {}
    for term in _search_words(mention):
        for m in re.finditer(re.escape(term), text, re.IGNORECASE):
            for s_start, s_end, sentence in sentences:
                if s_start <= m.start() < s_end:
                    matched[s_start] = sentence
    return " ".join(matched[k] for k in sorted(matched))
