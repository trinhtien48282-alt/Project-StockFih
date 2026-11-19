import itertools

import chess
import pytest

from stockfih.engine.match import (
    OPENINGS,
    GameResult,
    MatchSummary,
    _opening_board,
    play_game,
    play_match,
    summarize,
)
from stockfih.engine.stockfih import StockFihEngine


class Scripted:
    # Plays the given UCI moves in order. Pass itertools.cycle(...) to repeat forever.
    def __init__(self, ucis):
        self._moves = iter(ucis)

    def choose_move(self, board):
        return chess.Move.from_uci(next(self._moves))


def test_every_opening_is_legal():
    for line in OPENINGS:
        assert not _opening_board(line).is_game_over()


def test_fools_mate_black_wins():
    result, plies, adjudicated = play_game(
        Scripted(["f2f3", "g2g4"]), Scripted(["e7e5", "d8h4"]), chess.Board()
    )
    assert (result, plies, adjudicated) == ("0-1", 4, False)


def test_ply_cap_scores_a_draw_and_says_so():
    white = Scripted(itertools.cycle(["b1c3", "c3b1"]))
    black = Scripted(itertools.cycle(["b8c6", "c6b8"]))
    result, plies, adjudicated = play_game(white, black, chess.Board(), max_plies=2)
    assert (result, plies, adjudicated) == ("1/2-1/2", 2, True)


def test_repetition_ends_the_game_before_the_cap():
    white = Scripted(itertools.cycle(["g1f3", "f3g1"]))
    black = Scripted(itertools.cycle(["g8f6", "f6g8"]))
    result, plies, adjudicated = play_game(white, black, chess.Board(), max_plies=50)
    assert result == "1/2-1/2" and adjudicated is False and plies <= 8


def test_illegal_engine_move_raises():
    with pytest.raises(ValueError):
        play_game(Scripted(["e2e5"]), Scripted(["e7e5"]), chess.Board())


def test_start_board_is_not_changed():
    start = chess.Board()
    play_game(Scripted(["f2f3", "g2g4"]), Scripted(["e7e5", "d8h4"]), start)
    assert start.fen() == chess.STARTING_FEN


@pytest.mark.parametrize(
    "result, a_is_white, score",
    [
        ("1-0", True, 1.0),
        ("1-0", False, 0.0),
        ("0-1", True, 0.0),
        ("0-1", False, 1.0),
        ("1/2-1/2", True, 0.5),
        ("1/2-1/2", False, 0.5),
    ],
)
def test_a_score(result, a_is_white, score):
    assert GameResult(0, a_is_white, result, 10, False).a_score == score


def test_summary_counts():
    games = [
        GameResult(0, True, "1-0", 10, False),  # A wins
        GameResult(0, False, "1-0", 10, False),  # A loses
        GameResult(1, True, "1/2-1/2", 200, True),  # capped draw
    ]
    s = summarize(games)
    assert (s.wins, s.draws, s.losses, s.adjudicated) == (1, 1, 1, 1)
    assert s.games == 3 and s.score == 0.5


def test_score_is_none_without_games():
    assert MatchSummary(0, 0, 0, 0).score is None


def test_match_plays_each_opening_with_both_colours():
    seen = []
    results = play_match(
        lambda: StockFihEngine(depth=1, seed=1),
        lambda: StockFihEngine(depth=1, seed=2),
        OPENINGS[:2],
        max_plies=6,
        on_game=seen.append,
    )
    assert results == seen
    assert [(g.opening, g.a_is_white) for g in results] == [(0, True), (0, False), (1, True), (1, False)]
    assert all(g.plies <= 6 for g in results)
