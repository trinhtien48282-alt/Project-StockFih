import random

import chess
import pytest

from stockfih.personality.commentary import Commentator
from stockfih.personality.events import EventKind as K
from stockfih.personality.events import GameEvent
from stockfih.personality.frequency import FREQUENCIES, Pacer

DIALOGUE = {
    "professional": {
        "player": {
            "capture": ["took a {captured}", "grabbed a {captured}"],
            "checkmate": ["mate"],
        }
    }
}


class _Rng:
    # Stand-in for the pacer's roll: random() always returns `value`.
    def __init__(self, value: float = 0.0) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


def commentator(mode: str = "professional") -> Commentator:
    return Commentator(mode, DIALOGUE, random.Random(0))


def pacer(level: str, value: float = 0.0, mode: str = "professional") -> Pacer:
    return Pacer(commentator(mode), level, rng=_Rng(value))


def cap() -> list[GameEvent]:
    return [GameEvent(K.CAPTURE, "player", 1, "exd5", chess.WHITE, captured=chess.PAWN)]


def mate() -> list[GameEvent]:
    return [GameEvent(K.CHECKMATE, "player", 9, "Qxf7", chess.WHITE, winner=chess.WHITE)]


# --- levels ---


def test_levels_are_the_four_roadmap_names():
    assert set(FREQUENCIES) == {"silent", "normal", "chaotic", "unhinged"}


def test_silent_never_speaks_even_for_checkmate():
    assert pacer("silent").comment(mate(), ply=9) is None
    assert pacer("silent").comment(cap(), ply=1) is None


def test_unknown_level_is_refused_and_old_level_kept():
    p = pacer("normal")
    with pytest.raises(ValueError):
        p.set_level("loud")
    assert p.level == "normal"


def test_silent_mode_still_says_nothing():
    assert pacer("unhinged", mode="silent").comment(mate(), ply=9) is None


# --- chance and cooldown ---


def test_game_ending_event_bypasses_chance_and_cooldown():
    # Chance roll would fail (0.99 >= 0.35), yet the checkmate line is still said.
    assert pacer("normal", value=0.99).comment(mate(), ply=9) == "mate"


def test_ordinary_event_needs_the_chance_roll():
    assert pacer("normal", value=0.99).comment(cap(), ply=3) is None
    assert pacer("normal", value=0.0).comment(cap(), ply=3) is not None


def test_cooldown_blocks_ordinary_lines_until_min_gap_passes():
    p = pacer("normal", value=0.0)  # normal: min_gap 6
    assert p.comment(cap(), ply=3) is not None
    assert p.comment(cap(), ply=5) is None  # only 2 plies later
    assert p.comment(cap(), ply=9) is not None  # 6 plies later


def test_cooldown_does_not_block_game_ending_lines():
    p = pacer("normal", value=0.0)
    assert p.comment(cap(), ply=3) is not None
    assert p.comment(mate(), ply=4) == "mate"


def test_unhinged_speaks_every_ordinary_event():
    p = pacer("unhinged", value=0.99)  # min_gap 0, chance 1.0
    assert all(p.comment(cap(), ply=i) is not None for i in range(1, 6))


def test_chaotic_has_a_shorter_cooldown_than_normal():
    p = pacer("chaotic", value=0.0)  # min_gap 2
    assert p.comment(cap(), ply=3) is not None
    assert p.comment(cap(), ply=4) is None
    assert p.comment(cap(), ply=5) is not None


# --- history ---


def test_recent_line_is_avoided_while_another_fits():
    p = pacer("unhinged", value=0.0)
    first = p.comment(cap(), ply=1)
    second = p.comment(cap(), ply=2)
    assert {first, second} == {"took a pawn", "grabbed a pawn"}


def test_when_every_line_is_recent_one_is_still_said():
    p = pacer("unhinged", value=0.0)
    p.comment(cap(), ply=1)
    p.comment(cap(), ply=2)
    assert p.comment(cap(), ply=3) in {"took a pawn", "grabbed a pawn"}


def test_commentator_avoid_skips_a_recent_line():
    c = commentator()
    for _ in range(20):
        assert c.comment(cap(), avoid={"took a pawn"}) == "grabbed a pawn"


def test_reset_clears_cooldown_and_history():
    p = pacer("normal", value=0.0)
    p.comment(cap(), ply=3)
    p.reset()
    assert p.comment(cap(), ply=4) is not None  # would be blocked without reset
