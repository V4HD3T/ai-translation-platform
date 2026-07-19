"""Unit tests for language-aware case folding -- the Turkish İ/I problem
in particular. See app/services/text_normalization.py for why plain
str.lower()/casefold() gets Turkish wrong."""

from app.services.text_normalization import fold_case


def test_turkish_dotted_capital_folds_to_plain_i():
    assert fold_case("YEDİ", "tr") == "yedi"


def test_turkish_dotless_capital_folds_to_dotless_i():
    assert fold_case("BAŞINI", "tr") == "başını"


def test_turkish_mixed_sentence():
    assert fold_case("DİLİNİN ALTINDA", "tr") == "dilinin altında"


def test_turkish_folding_makes_upper_and_lower_forms_equal():
    assert fold_case("BAŞINI YE", "tr") == fold_case("başını ye", "tr")


def test_default_folding_without_language_code():
    assert fold_case("HELLO") == "hello"


def test_german_sharp_s_folds_equal():
    # casefold (unlike lower) maps ß -> ss, so these compare equal --
    # relevant for future German fill-blank answers.
    assert fold_case("Straße", "de") == fold_case("STRASSE", "de")


def test_non_turkish_ascii_i_is_untouched():
    # The Turkish mapping must not leak into other languages.
    assert fold_case("KIND", "de") == "kind"
