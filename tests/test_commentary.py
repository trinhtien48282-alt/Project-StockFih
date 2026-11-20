import json
import random

import chess
import pytest

from stockfih.personality.commentary import (
    DIALOGUE_PATH,
    MODES,
    Commentator,
    check_dialogue,
    load_dialogue,
)
from stockfih.personality.events import EventKind as K
from stockfih.personality.events import GameEvent, events_for_move
from stockfih.personality.game_events import FactEvent
from stockfih.personality.judgement import judgement_event


def ev(kind, by="player", **extra):
    return GameEvent(kind, by, 1, "e4", chess.WHITE, **extra)


def commentator(lines, mode="toxic_comedian", seed=0):
    return Commentator(mode, {"toxic_comedian": lines}, random.Random(seed))


# --- the shipped dialogue file ---


def test_shipped_dialogue_is_valid():
    data = load_dialogue()
    assert set(data) == {"toxic_comedian", "professional"}


@pytest.mark.parametrize("mode", ["toxic_comedian", "professional"])
@pytest.mark.parametrize("by", ["player", "stockfih"])
@pytest.mark.parametrize("kind", ["inaccuracy", "mistake", "blunder", "missed_win", "capture", "check", "checkmate"])
def test_shipped_modes_cover_the_main_events(mode, by, kind):
    assert load_dialogue()[mode][by][kind]


@pytest.mark.parametrize("mode", ["toxic_comedian", "professional"])
def test_plain_moves_get_no_comment(mode):
    events = events_for_move(chess.Board(), chess.Move.from_uci("e2e4"), "player")
    assert Commentator(mode).comment(events) is None


def test_real_checkmate_gets_a_finished_line():
    board = chess.Board()
    for san in ("f3", "e5", "g4"):
        board.push_san(san)
    events = events_for_move(board, chess.Move.from_uci("d8h4"), "stockfih")
    for mode in ("toxic_comedian", "professional"):
        line = Commentator(mode, rng=random.Random(1)).comment(events)
        assert line and "{" not in line and "}" not in line


class _First:
    # Stand-in rng: always the first usable line, so the test is repeatable.
    def choice(self, seq):
        return seq[0]


def test_professional_blunder_uses_the_measured_loss():
    event = judgement_event(chess.Board(), chess.Move.from_uci("e2e4"), "player", 0, -250)
    assert Commentator("professional", rng=_First()).comment([event]) == (
        "e4 is a blunder by the engine's evaluation, about 250 centipawns."
    )


def test_mate_blunder_has_no_loss_so_no_invented_number():
    event = judgement_event(chess.Board(), chess.Move.from_uci("e2e4"), "player", 0, -99_997)
    assert event.loss is None
    line = Commentator("professional").comment([event])
    assert line == "e4 is a blunder by the engine's evaluation."


# --- modes ---


def test_silent_says_nothing():
    c = Commentator("silent", rng=random.Random(0))
    assert c.comment([ev(K.CHECKMATE, winner=chess.WHITE)]) is None


def test_mode_can_change_and_bad_mode_is_refused():
    c = Commentator("professional")
    c.set_mode("silent")
    assert c.mode == "silent"
    with pytest.raises(ValueError):
        c.set_mode("angry")
    assert c.mode == "silent"
    with pytest.raises(ValueError):
        Commentator("angry")


def test_all_modes_are_accepted():
    for mode in MODES:
        assert Commentator(mode).mode == mode


# --- line choice ---


def test_values_are_filled_from_the_event():
    c = commentator({"player": {"capture": ["took a {captured}"]}})
    assert c.comment([ev(K.CAPTURE, captured=chess.QUEEN)]) == "took a queen"


def test_speaker_decides_which_lines_are_used():
    lines = {"player": {"check": ["player line"]}, "stockfih": {"check": ["engine line"]}}
    c = commentator(lines)
    assert c.comment([ev(K.CHECK, by="player")]) == "player line"
    assert c.comment([ev(K.CHECK, by="stockfih")]) == "engine line"


def test_line_needing_a_missing_value_is_skipped():
    c = commentator({"player": {"blunder": ["lost {loss}", "no number here"]}})
    assert c.comment([ev(K.BLUNDER)]) == "no number here"
    assert c.comment([ev(K.BLUNDER, loss=120)]) in ("lost 120", "no number here")


def test_only_unusable_lines_means_next_event_or_nothing():
    lines = {"player": {"blunder": ["lost {loss}"], "check": ["check line"]}}
    c = commentator(lines)
    assert c.comment([ev(K.BLUNDER), ev(K.CHECK)]) == "check line"
    assert c.comment([ev(K.BLUNDER)]) is None


def test_priority_prefers_the_bigger_event():
    lines = {"player": {"capture": ["capture line"], "checkmate": ["mate line"]}}
    c = commentator(lines)
    events = [ev(K.MOVE), ev(K.CAPTURE, captured=chess.PAWN), ev(K.CHECKMATE, winner=chess.WHITE)]
    assert c.comment(events) == "mate line"


def test_game_facts_use_the_game_speaker():
    c = commentator({"game": {"opening": ["Opening {text}"], "game_won": ["you won"]}})
    assert c.comment([FactEvent(K.OPENING, "Ruy Lopez")]) == "Opening Ruy Lopez"
    assert c.comment([FactEvent(K.GAME_WON)]) == "you won"


def test_same_seed_gives_the_same_lines():
    lines = {"player": {"check": ["a", "b", "c", "d"]}}
    first = [commentator(lines, seed=5).comment([ev(K.CHECK)]) for _ in range(3)]
    again = [commentator(lines, seed=5).comment([ev(K.CHECK)]) for _ in range(3)]
    assert first == again


# --- dialogue checking ---


@pytest.mark.parametrize(
    "bad",
    [
        [],
        {"angry": {}},
        {"silent": {}},
        {"toxic_comedian": {"nobody": {}}},
        {"toxic_comedian": {"player": {"not_an_event": ["x"]}}},
        {"toxic_comedian": {"player": {"check": []}}},
        {"toxic_comedian": {"player": {"check": [5]}}},
        {"toxic_comedian": {"player": {"check": ["  "]}}},
        {"toxic_comedian": {"player": {"check": ["hi {nope}"]}}},
        {"toxic_comedian": {"player": {"check": ["hi {san.__class__}"]}}},
        {"toxic_comedian": {"player": {"check": ["hi {}"]}}},
        {"toxic_comedian": {"player": {"check": ["hi {san!r}"]}}},
        {"toxic_comedian": {"player": {"check": ["hi {san:>999}"]}}},
        {"toxic_comedian": {"player": {"check": ["broken {"]}}},
    ],
)
def test_bad_dialogue_is_rejected(bad):
    with pytest.raises(ValueError):
        check_dialogue(bad)


def test_commentator_rejects_bad_dialogue():
    with pytest.raises(ValueError):
        Commentator("toxic_comedian", {"toxic_comedian": {"player": {"check": ["{nope}"]}}})


def test_load_dialogue_reports_unreadable_files(tmp_path):
    with pytest.raises(ValueError):
        load_dialogue(tmp_path / "missing.json")
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_dialogue(broken)


def test_load_dialogue_reads_a_custom_file(tmp_path):
    path = tmp_path / "d.json"
    path.write_text(json.dumps({"professional": {"player": {"check": ["ok"]}}}), encoding="utf-8")
    assert load_dialogue(path)["professional"]["player"]["check"] == ["ok"]


def test_dialogue_file_ships_inside_resources():
    # The Windows build bundles src/stockfih/resources, so the file must live there.
    assert DIALOGUE_PATH.parent.name == "resources"
    assert DIALOGUE_PATH.is_file()
