"""
Language-aware case folding for text comparison.

The problem this solves: Python's `str.lower()` / `str.casefold()` use the
Unicode *default* case mappings, and Turkish is the textbook case where
those defaults are wrong. Turkish has two distinct I-letters, each with its
own upper/lower pair:

    İ (dotted capital)  <->  i (dotted small)
    I (dotless capital) <->  ı (dotless small)

Unicode's default mapping, however, says `"I".lower() == "i"` and
`"İ".lower() == "i̇"` (an `i` followed by a *combining dot above*,
U+0307). Both results break plain substring/equality comparison against
correctly-written lowercase Turkish:

    "BAŞINI".lower()  -> "başini"        ("başını" not found)
    "DİLİNİN".lower() -> "di̇li̇ni̇n"    ("dilinin" not found)

Concretely, before this module existed, typing a Turkish idiom in capital
letters ("BAŞINI YEDİ") silently produced no idiom warning, and any future
Turkish fill-blank quiz answer typed with caps lock on would have been
marked wrong. For a language-learning platform whose author's own language
is Turkish, that's not an edge case worth ignoring.

The fix is the standard one: apply the Turkish-specific capital mappings
*before* the generic casefold. For every other language, plain
`str.casefold()` is used — which is also a small upgrade over the previous
`str.lower()` calls (e.g. German "Straße" and "STRASSE" now fold to the
same string, "strasse").
"""

_TURKISH_CAPITALS = str.maketrans({"İ": "i", "I": "ı"})


def fold_case(text: str, language_code: str | None = None) -> str:
    """Case-folds `text` for comparison purposes, using Turkish-specific
    İ/I mappings when `language_code` is "tr" and Unicode default folding
    otherwise. Comparisons should fold *both* sides with the same
    language code."""
    if language_code == "tr":
        text = text.translate(_TURKISH_CAPITALS)
    return text.casefold()
