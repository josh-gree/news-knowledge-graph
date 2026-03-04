from news_kg.utils import extract_sentence_context


def test_returns_matching_sentence():
    text = "The sky is blue. Barack Obama spoke today. The weather was fine."
    result = extract_sentence_context(text, "Barack Obama")
    assert "Barack Obama spoke today." in result


def test_partial_name_matches_sentences():
    text = "The sky is blue. Donald Trump arrived. Later, Trump spoke to reporters."
    result = extract_sentence_context(text, "Donald Trump")
    assert "Donald Trump arrived." in result
    assert "Trump spoke to reporters." in result


def test_returns_empty_string_when_no_match():
    text = "The sky is blue. The weather was fine."
    result = extract_sentence_context(text, "Barack Obama")
    assert result == ""


def test_mention_at_start_of_text():
    text = "London is a city. It is large."
    result = extract_sentence_context(text, "London")
    assert "London is a city." in result


def test_case_insensitive_match():
    text = "The prime minister spoke. BORIS JOHNSON left the room."
    result = extract_sentence_context(text, "Boris Johnson")
    assert "BORIS JOHNSON left the room." in result
