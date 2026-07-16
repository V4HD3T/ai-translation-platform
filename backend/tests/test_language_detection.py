from app.services.language_detection import detect_language

# Every phrase below was manually verified against the actual classifier
# before being used as a test fixture (see the module docstring in
# language_detection.py for why short phrases are excluded here).
LONG_UNAMBIGUOUS_PHRASES = {
    "en": "Hello, how are you doing today?",
    "es": "¡Hola! ¿Cómo estás hoy?",
    "fr": "Je ne parle pas très bien français.",
    "de": "Ich möchte gerne einen Kaffee bestellen.",
    "tr": "Bugün hava çok güzel görünüyor.",
}


def test_detect_language_on_clear_sentences():
    for expected_code, text in LONG_UNAMBIGUOUS_PHRASES.items():
        result = detect_language(text)
        assert result.language_code == expected_code, f"failed for: {text!r}"
        assert result.is_reliable is True
        assert 0.0 <= result.confidence <= 1.0


def test_detect_language_short_text_is_never_reliable():
    # Regardless of what the raw classifier says, short input shouldn't be
    # trusted -- this is the whole point of the length guard.
    result = detect_language("hi")
    assert result.is_reliable is False


def test_detect_language_empty_text():
    result = detect_language("")
    assert result.is_reliable is False
    assert result.confidence == 0.0


def test_detect_language_whitespace_only():
    result = detect_language("   ")
    assert result.is_reliable is False


def test_detect_language_only_returns_supported_codes():
    # The classifier is restricted to the app's own language list, so it
    # should never suggest switching to an unsupported language.
    from app.services.translation_service import NLLB_LANGUAGE_CODES

    result = detect_language(LONG_UNAMBIGUOUS_PHRASES["de"])
    assert result.language_code in NLLB_LANGUAGE_CODES


def test_detect_language_endpoint(client):
    response = client.post(
        "/detect-language", json={"text": LONG_UNAMBIGUOUS_PHRASES["fr"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["language_code"] == "fr"
    assert data["is_reliable"] is True


def test_detect_language_endpoint_short_text_flagged_unreliable(client):
    response = client.post("/detect-language", json={"text": "hi"})
    assert response.status_code == 200
    assert response.json()["is_reliable"] is False


def test_detect_language_endpoint_rejects_empty_text(client):
    response = client.post("/detect-language", json={"text": ""})
    assert response.status_code == 422  # min_length=1 validation
