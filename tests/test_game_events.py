import pytest

from stockfih.personality.events import EventKind as K
from stockfih.personality.game_events import (
    OPENING_MAX_CHARS,
    SWING_CP,
    major_swing,
    opening_from_headers,
    result_for_player,
)
from stockfih.personality.judgement import MATE_BOUND


def test_swing_threshold_edges():
    assert major_swing(0, SWING_CP - 1) is None
    assert major_swing(0, SWING_CP).kind == K.MAJOR_SWING


def test_swing_direction_is_named():
    assert major_swing(0, 250).text == "white"
    assert major_swing(0, -250).text == "black"
    assert major_swing(-100, 150).text == "white"


def test_swing_skips_mate_scores():
    assert major_swing(0, MATE_BOUND) is None
    assert major_swing(-MATE_BOUND, 0) is None


@pytest.mark.parametrize(
    "result, color, kind",
    [
        ("1-0", "white", K.GAME_WON),
        ("1-0", "black", K.GAME_LOST),
        ("0-1", "black", K.GAME_WON),
        ("0-1", "white", K.GAME_LOST),
        ("1/2-1/2", "white", K.GAME_DRAWN),
        ("1/2-1/2", "black", K.GAME_DRAWN),
    ],
)
def test_result_for_player(result, color, kind):
    assert result_for_player(result, color).kind == kind


@pytest.mark.parametrize(
    "result, color",
    [("*", "white"), ("1-0", ""), ("1-0", "green"), ("1-0", "?")],
)
def test_no_result_event_when_it_cannot_be_told(result, color):
    assert result_for_player(result, color) is None


def test_opening_name_is_taken_from_header_and_tidied():
    event = opening_from_headers({"Opening": "  Ruy   Lopez "})
    assert event.kind == K.OPENING and event.text == "Ruy Lopez"


def test_opening_falls_back_to_eco_code():
    assert opening_from_headers({"ECO": "C60"}).text == "C60"


def test_no_opening_without_headers():
    assert opening_from_headers({}) is None
    assert opening_from_headers({"Opening": "   "}) is None


def test_overlong_opening_name_is_refused():
    assert opening_from_headers({"Opening": "x" * (OPENING_MAX_CHARS + 1)}) is None
