import pytest

from app.evaluation.asr_eval import count, edit_distance, evaluate, normalize


def test_normalize() -> None:
    assert normalize("  Bonjour,  le MONDE ! ") == "bonjour le monde"
    assert normalize("ḍ") == "ḍ"  # NFC
    assert normalize("ḍ") != normalize("d")  # diacritiques conservés
    assert normalize("«a»—b") == "a b"


def test_edit_distance() -> None:
    assert edit_distance(list("kitten"), list("sitting")) == 3
    assert edit_distance([], ["a"]) == 1
    assert edit_distance(["a", "b"], ["a", "b"]) == 0


def test_wer_and_cer() -> None:
    c = count("un deux trois quatre", "un deux troi")
    assert c.words == 4 and c.word_errors == 2  # une substitution, une suppression
    assert c.wer == 0.5
    assert c.chars == 17 and c.char_errors == 7  # « undeuxtroisquatre »
    assert count("Même, phrase.", "même phrase").wer == 0.0


def test_evaluate_breakdown() -> None:
    rows = [
        {"id": "1", "reference": "a b", "hypothesis": "a b", "speaker": "s1", "condition": "calme"},
        {"id": "2", "reference": "a b", "hypothesis": "a", "speaker": "s2", "condition": "bruit"},
    ]
    totals = evaluate(rows)
    assert totals["global"].wer == 0.25  # erreurs cumulées sur le corpus, pas moyenne
    assert totals["speaker=s1"].wer == 0.0
    assert totals["condition=bruit"].wer == 0.5
    with pytest.raises(ValueError):
        evaluate([{"id": "x", "reference": " ? ", "hypothesis": ""}])
