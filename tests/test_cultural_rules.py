import random

import pytest

from stockfih.personality.commentary import Commentator, load_dialogue
from stockfih.personality.cultural_rules import COUNTRIES, NAME_ORIGINS, CulturalSettings, identity_event
from stockfih.personality.events import EventKind as K


def on(country, origin) -> CulturalSettings:
    return CulturalSettings(enabled=True, country=country, origin=origin)


# --- rules ---


def test_off_by_default():
    assert identity_event(CulturalSettings()) is None
    assert identity_event(CulturalSettings(country="VN", origin="vietnamese")) is None


def test_matching_settings_give_a_match():
    event = identity_event(on("VN", "vietnamese"))
    assert event.kind is K.IDENTITY_MATCH
    assert (event.country, event.origin) == ("Vietnam", "Vietnamese")


def test_different_settings_give_a_mismatch():
    event = identity_event(on("VN", "japanese"))
    assert event.kind is K.IDENTITY_MISMATCH
    assert (event.country, event.origin) == ("Vietnam", "Japanese")


def test_origin_with_two_home_countries_matches_both():
    assert identity_event(on("US", "english")).kind is K.IDENTITY_MATCH
    assert identity_event(on("GB", "english")).kind is K.IDENTITY_MATCH
    assert identity_event(on("MX", "spanish")).kind is K.IDENTITY_MATCH


@pytest.mark.parametrize(
    "country, origin",
    [
        (None, "japanese"),
        ("JP", None),
        (None, None),
        ("", "japanese"),
        ("ZZ", "japanese"),  # not in the table
        ("JP", "klingon"),  # not in the table
    ],
)
def test_missing_or_unknown_settings_give_nothing(country, origin):
    assert identity_event(on(country, origin)) is None


def test_stored_values_are_normalised():
    event = identity_event(on(" vn ", " Vietnamese "))
    assert event.kind is K.IDENTITY_MATCH


def test_tables_agree_with_each_other():
    homes = set().union(*(h for _label, h in NAME_ORIGINS.values()))
    assert homes <= set(COUNTRIES)  # every home country has a display name
    assert set(COUNTRIES) <= homes  # every country has at least one origin to compare with
    assert all(len(code) == 2 and code.isupper() for code in COUNTRIES)


# --- commentary ---


@pytest.mark.parametrize("seed", range(10))
def test_toxic_lines_name_both_settings(seed):
    c = Commentator("toxic_comedian", rng=random.Random(seed))
    for country, origin in (("VN", "japanese"), ("VN", "vietnamese")):
        line = c.comment([identity_event(on(country, origin))])
        assert line and "{" not in line
        assert COUNTRIES[country] in line
        assert NAME_ORIGINS[origin][0] in line


def test_professional_and_silent_make_no_identity_comment():
    event = identity_event(on("VN", "japanese"))
    assert Commentator("professional").comment([event]) is None
    assert Commentator("silent").comment([event]) is None


def test_shipped_dialogue_has_identity_lines_for_toxic_only():
    data = load_dialogue()
    for kind in ("identity_match", "identity_mismatch"):
        assert data["toxic_comedian"]["game"][kind]
        assert kind not in data["professional"].get("game", {})
