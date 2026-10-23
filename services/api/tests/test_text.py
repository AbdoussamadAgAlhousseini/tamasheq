import unicodedata

import pytest

from app.text import detect_script, normalize, search_key


def test_normalize_composes_and_collapses_spaces() -> None:
    decomposed = "ḍ"  # d + point souscrit combinant
    assert normalize(f"  {decomposed}\t\n x  ") == "ḍ x"  # ḍ précomposé
    assert unicodedata.is_normalized("NFC", normalize(decomposed))


def test_search_key_ignores_case_but_keeps_diacritics() -> None:
    assert search_key("ABC") == search_key("abc")
    assert search_key("Ḍ") == search_key("ḍ")
    assert search_key("ḍ") != search_key("d")
    assert search_key("ɣ") != search_key("g")
    assert search_key("Ǝ") == search_key("ǝ")


def test_tifinagh_has_no_case_and_is_unchanged() -> None:
    text = "ⵜⴰ"
    assert search_key(text) == text


@pytest.mark.parametrize(
    ("text", "script"),
    [
        ("abc", "Latn"),
        ("ḍǝɣš", "Latn"),
        ("ḍ", "Latn"),
        ("ⵜⴰ ⵍ", "Tfng"),
        ("ⵜⴰ, 12 !", "Tfng"),
        ("ab ⵜ", "mixed"),
        ("abc ا", "mixed"),
        ("123 ?", "none"),
    ],
)
def test_detect_script(text: str, script: str) -> None:
    assert detect_script(text) == script
