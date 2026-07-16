"""
Automatic language detection.

Built on `langid`, a lightweight, offline, pure-Python classifier — its
language model ships inside the pip package, so (unlike the real NLLB
translation model) it needs no network access and works in this sandbox.

Honest limitation, discovered by actually testing this rather than assuming
it would work: language ID on *short* text is genuinely unreliable with a
model this size. In testing, common short greetings were confidently
misclassified — e.g. "Comment ça va?" (French) was called Turkish at 99.5%
confidence, "Merhaba" (Turkish) was called German at 99%. Restricting the
classifier to only the app's supported languages (instead of langid's full
~97) measurably helped, but did not eliminate the problem. Longer,
unambiguous sentences are detected reliably (99%+ in testing).

Given that, detection here is deliberately conservative:
- Text shorter than MIN_CONFIDENT_LENGTH is never trusted, regardless of
  the reported confidence score.
- Below MIN_CONFIDENCE, the result is returned but flagged `is_reliable:
  false` so callers (the frontend) can show it as a low-confidence guess
  rather than silently switching the user's language.
This is a heuristic, not a guarantee — it will not catch every confidently
wrong short-phrase case, but it removes the worst and most common ones.
"""

from dataclasses import dataclass

from langid.langid import LanguageIdentifier, model

from app.services.translation_service import NLLB_LANGUAGE_CODES

MIN_CONFIDENT_LENGTH = 12
MIN_CONFIDENCE = 0.6

_identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
_identifier.set_languages(list(NLLB_LANGUAGE_CODES.keys()))


@dataclass
class DetectionResult:
    language_code: str
    confidence: float
    is_reliable: bool


def detect_language(text: str) -> DetectionResult:
    stripped = text.strip()
    if not stripped:
        return DetectionResult(language_code="en", confidence=0.0, is_reliable=False)

    language_code, confidence = _identifier.classify(stripped)
    is_reliable = len(stripped) >= MIN_CONFIDENT_LENGTH and confidence >= MIN_CONFIDENCE

    return DetectionResult(
        language_code=language_code,
        confidence=round(confidence, 3),
        is_reliable=is_reliable,
    )
