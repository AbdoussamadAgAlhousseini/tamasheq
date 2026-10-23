"""Traitements de texte neutres vis-à-vis des conventions orthographiques.

Seules des opérations définies par Unicode sont appliquées ici. Aucune règle propre au
tamasheq (équivalences de lettres, translittération latin ↔ tifinagh) n'est codée : ces règles
dépendent des conventions retenues par les locuteurs (décision D4) et seront des données
versionnées, pas du code.
"""

import re
import unicodedata
from typing import Literal

TIFINAGH = range(0x2D30, 0x2D80)  # bloc Unicode Tifinagh U+2D30–U+2D7F

_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Forme stockée : NFC et espaces normalisés. Ne modifie aucune lettre."""
    return _SPACES.sub(" ", unicodedata.normalize("NFC", text)).strip()


def search_key(text: str) -> str:
    """Clé de recherche : forme normalisée sans distinction de casse.

    Les signes diacritiques sont conservés : en écriture latine du tamasheq, des lettres comme
    ɣ, ǝ, ḍ, ṭ ou š peuvent distinguer des mots ; les confondre serait une décision
    linguistique qui ne relève pas de ce code.
    """
    return unicodedata.normalize("NFC", normalize(text).casefold())


Script = Literal["Latn", "Tfng"]


def detect_script(text: str) -> Script | Literal["mixed", "none"]:
    """Écriture des lettres présentes (les chiffres, espaces et ponctuation sont ignorés)."""
    scripts: set[str] = set()
    for char in text:
        if ord(char) in TIFINAGH:
            scripts.add("Tfng")
        elif unicodedata.category(char).startswith(("L", "M")):
            scripts.add("Latn" if _is_latin(char) else "other")
    if not scripts:
        return "none"
    if scripts == {"Tfng"}:
        return "Tfng"
    if scripts == {"Latn"}:
        return "Latn"
    return "mixed"


def _is_latin(char: str) -> bool:
    if unicodedata.category(char).startswith("M"):
        return True  # signe combinant : rattaché à la lettre qui précède
    name = unicodedata.name(char, "")
    return name.startswith("LATIN ") or name.startswith("MODIFIER LETTER")
