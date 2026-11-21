import json

import pytest

from stockfih.personality.commentary import MODES
from stockfih.personality.cultural_rules import COUNTRIES, NAME_ORIGINS, CulturalSettings
from stockfih.personality.frequency import FREQUENCIES
from stockfih.personality.settings import (
    LANGUAGES,
    MAX_ELO,
    MIN_ELO,
    PROFANITY_LEVELS,
    PersonalitySettings,
)

S = PersonalitySettings


def test_defaults():
    s = S()
    assert s.mode == "toxic_comedian"
    assert s.frequency == "normal"
    assert s.profanity == "mild"
    assert s.elo_personality is True
    assert s.cultural is False  # identity jokes are opt-in
    assert s.country == "" and s.origin == ""
    assert s.alien is True
    assert s.language == "en"
    assert s.muted is False
    assert s.stockfih_elo is None  # never invented


def test_defaults_are_all_valid_choices():
    s = S()
    assert s.mode in MODES
    assert s.frequency in FREQUENCIES
    assert s.profanity in PROFANITY_LEVELS
    assert s.language in LANGUAGES


def test_round_trip():
    s = S(
        mode="professional",
        frequency="unhinged",
        profanity="spicy",
        elo_personality=False,
        cultural=True,
        country="VN",
        origin="japanese",
        alien=False,
        muted=True,
        stockfih_elo=1500,
    )
    assert S.from_json(s.to_json()) == s


def test_every_choice_survives_a_round_trip():
    for mode in MODES:
        assert S.from_json(S(mode=mode).to_json()).mode == mode
    for level in FREQUENCIES:
        assert S.from_json(S(frequency=level).to_json()).frequency == level
    for level in PROFANITY_LEVELS:
        assert S.from_json(S(profanity=level).to_json()).profanity == level
    for code in COUNTRIES:
        assert S.from_json(S(country=code).to_json()).country == code
    for key in NAME_ORIGINS:
        assert S.from_json(S(origin=key).to_json()).origin == key


@pytest.mark.parametrize("text", ["", "not json", "[]", "null", "42", '"x"', None])
def test_bad_text_gives_defaults(text):
    assert S.from_json(text) == S()


def test_unknown_values_fall_back_field_by_field():
    text = json.dumps(
        {"mode": "angry", "frequency": "unhinged", "profanity": 5, "country": "ZZ", "origin": ["x"]}
    )
    s = S.from_json(text)
    assert s.mode == "toxic_comedian"  # bad, default
    assert s.frequency == "unhinged"  # good, kept
    assert s.profanity == "mild"
    assert s.country == "" and s.origin == ""


def test_flags_must_be_real_booleans():
    s = S.from_json(json.dumps({"cultural": 1, "alien": "no", "muted": "yes", "elo_personality": None}))
    assert s == S()


def test_missing_keys_use_defaults():
    assert S.from_json("{}") == S()


@pytest.mark.parametrize("bad", [0, 99, -5, MAX_ELO + 1, 1500.5, "1500", True, None])
def test_assumed_rating_out_of_range_or_wrong_type_is_dropped(bad):
    assert S.from_json(json.dumps({"stockfih_elo": bad})).stockfih_elo is None


@pytest.mark.parametrize("good", [MIN_ELO, 1500, MAX_ELO])
def test_assumed_rating_in_range_is_kept(good):
    assert S.from_json(json.dumps({"stockfih_elo": good})).stockfih_elo == good


def test_only_english_dialogue_is_offered():
    assert set(LANGUAGES) == {"en"}
    assert S.from_json(json.dumps({"language": "fr"})).language == "en"


def test_to_cultural():
    assert S().to_cultural() == CulturalSettings(enabled=False, country=None, origin=None)
    s = S(cultural=True, country="VN", origin="japanese")
    assert s.to_cultural() == CulturalSettings(enabled=True, country="VN", origin="japanese")
