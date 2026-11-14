from stockfih.profiles.player import GameRecord
from stockfih.profiles.statistics import compute, outcome_for


def rec(result: str, color: str) -> GameRecord:
    return GameRecord(0, "2026-11-14 12:00", "A", "B", result, "pgn", color)


def test_outcome_for():
    assert outcome_for("1-0", "white") == "win"
    assert outcome_for("1-0", "black") == "loss"
    assert outcome_for("0-1", "black") == "win"
    assert outcome_for("0-1", "white") == "loss"
    assert outcome_for("1/2-1/2", "white") == "draw"
    assert outcome_for("1/2-1/2", "") == "draw"
    assert outcome_for("1-0", "") is None
    assert outcome_for("*", "white") is None


def test_compute_counts_and_win_rate():
    s = compute([rec("1-0", "white"), rec("1-0", "black"), rec("0-1", "black"), rec("1/2-1/2", "white")])
    assert (s.total, s.wins, s.losses, s.draws, s.unscored) == (4, 2, 1, 1, 0)
    assert s.win_rate == 0.5


def test_empty_has_no_win_rate():
    s = compute([])
    assert s.total == 0 and s.win_rate is None


def test_unknown_color_decisive_game_is_unscored():
    s = compute([rec("1-0", ""), rec("1-0", "white")])
    assert (s.total, s.wins, s.unscored) == (2, 1, 1)
    assert s.win_rate == 1.0
