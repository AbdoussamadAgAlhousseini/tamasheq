import pytest
from pydantic import ValidationError

from app.models import Script
from app.schemas import CorpusTextIn, LexicalEntryIn

# Données factices : chaînes de test, pas du tamasheq.
RIGHTS = {"license": "CC-BY-4.0", "allow_publication": True, "allow_training": False}
SENSE = {"translation_fr": "test"}


def entry(**kw: object) -> LexicalEntryIn:
    return LexicalEntryIn.model_validate({"headword": "zzmot", "senses": [SENSE], **RIGHTS} | kw)


def test_script_is_detected_and_text_normalized() -> None:
    e = entry(headword="  zz\u0323mot  ")  # z + point souscrit combinant
    assert e.headword == "z\u1e93mot"  # NFC : le second z et le point deviennent ẓ
    assert e.script == Script.LATN
    assert entry(headword="ⴰⴱⴲ").script == Script.TFNG


@pytest.mark.parametrize(
    "kw",
    [
        {"headword": "zzⴰ"},  # mélange latin / tifinagh
        {"headword": "123"},  # aucune lettre
        {"headword": "zzmot", "script": "Tfng"},  # écriture déclarée contradictoire
        {"senses": []},
        {"senses": [{}]},  # sens sans définition ni traduction
        {"spellings": [{"form": "zzⴰ"}]},
        {"unknown_field": 1},
        {"language": "Tamasheq"},
    ],
)
def test_invalid_entries(kw: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        entry(**kw)


@pytest.mark.parametrize("missing", ["license", "allow_publication", "allow_training"])
def test_rights_are_explicit(missing: str) -> None:
    data = {"headword": "zzmot", "senses": [SENSE], **RIGHTS}
    del data[missing]
    with pytest.raises(ValidationError):
        LexicalEntryIn.model_validate(data)


def test_corpus_tifinagh_form_must_be_tifinagh() -> None:
    ok = CorpusTextIn.model_validate({"text": "zz test", "tifinagh_text": "ⴰ ⴱ", **RIGHTS})
    assert ok.script == Script.LATN
    with pytest.raises(ValidationError):
        CorpusTextIn.model_validate({"text": "zz", "tifinagh_text": "zz", **RIGHTS})
