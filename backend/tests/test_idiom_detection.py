from app.services.idiom_detection import find_idioms


def test_find_idioms_matches_known_phrase():
    matches = find_idioms("Break a leg tonight!", "en")
    assert len(matches) == 1
    assert matches[0].phrase == "break a leg"


def test_find_idioms_is_case_insensitive():
    matches = find_idioms("BREAK A LEG tonight!", "en")
    assert len(matches) == 1


def test_find_idioms_matches_multiple_phrases():
    matches = find_idioms(
        "It was a piece of cake, but I felt under the weather after.", "en"
    )
    phrases = {m.phrase for m in matches}
    assert phrases == {"piece of cake", "under the weather"}


def test_find_idioms_no_match_returns_empty_list():
    matches = find_idioms("The meeting starts at three o'clock.", "en")
    assert matches == []


def test_find_idioms_respects_language():
    # "en las nubes" is Spanish; shouldn't match when text is tagged English.
    matches = find_idioms("en las nubes", "en")
    assert matches == []
    matches_es = find_idioms("Últimamente siempre está en las nubes.", "es")
    assert len(matches_es) == 1


def test_find_idioms_unsupported_language_returns_empty_list():
    matches = find_idioms("anything at all", "zz")
    assert matches == []


def test_find_idioms_turkish_phrase_matches_despite_conjugation():
    # Dictionary key is the stable "içi içine sığma" stem (no verb ending),
    # specifically so it still matches conjugated forms like "sığmadı" here.
    matches = find_idioms("Sınav sonucunu görünce içi içine sığmadı.", "tr")
    assert len(matches) == 1
    assert matches[0].phrase == "içi içine sığma"


def test_find_idioms_turkish_uppercase_dotted_capital_i():
    # "YEDİ" contains İ (dotted capital I). Unicode default lowercasing
    # maps it to "i" + a combining dot (U+0307), which used to break the
    # substring match against the plain-"i" dictionary entry.
    matches = find_idioms("BAŞINI YEDİ resmen.", "tr")
    assert [m.phrase for m in matches] == ["başını ye"]


def test_find_idioms_turkish_uppercase_dotless_capital_i():
    # "ALTINDA" contains I (dotless capital I), which must fold to "ı",
    # not "i" -- plain .lower() produced "altinda" and never matched
    # "altında".
    matches = find_idioms("DİLİNİN ALTINDA bir şey var.", "tr")
    assert [m.phrase for m in matches] == ["dilinin altında"]
