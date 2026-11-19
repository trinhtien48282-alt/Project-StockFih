import chess
import pytest

from stockfih.engine.stockfih import (
    INF,
    MATE,
    StockFihEngine,
    _from_table,
    _to_table,
    negamax,
)

MATE_IN_TWO = "6k1/8/8/8/8/8/R7/1R4K1 w - - 0 1"
FREE_QUEEN = "4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1"
ROOKS = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"


@pytest.mark.parametrize("score", [0, 123, -450, MATE - 5, -MATE + 7])
@pytest.mark.parametrize("ply", [0, 1, 6])
def test_score_round_trip(score, ply):
    assert _from_table(_to_table(score, ply), ply) == score


def test_mate_score_moves_with_the_ply():
    # Mate delivered at ply 5, stored from a node at ply 3 (2 plies away), read at ply 1.
    stored = _to_table(MATE - 5, 3)
    assert _from_table(stored, 1) == MATE - 3


@pytest.mark.parametrize("fen, depth", [(MATE_IN_TWO, 3), (FREE_QUEEN, 3), (ROOKS, 2)])
def test_table_does_not_change_the_score(fen, depth):
    board = chess.Board(fen)
    before = board.fen()
    plain = negamax(board, depth, -INF, INF)
    with_table = negamax(board, depth, -INF, INF, 0, {})
    assert with_table == plain
    assert board.fen() == before


def test_table_reused_across_depths_is_still_exact():
    board = chess.Board(FREE_QUEEN)
    table: dict = {}
    negamax(board, 2, -INF, INF, 0, table)
    assert negamax(board, 3, -INF, INF, 0, table) == negamax(board, 3, -INF, INF)


def test_mate_in_two_score_is_exact_with_table():
    board = chess.Board(MATE_IN_TWO)
    assert negamax(board, 3, -INF, INF, 0, {}) == MATE - 3


def test_engine_fills_its_table():
    engine = StockFihEngine(depth=2, seed=1)
    assert len(engine.table) == 0
    engine.choose_move(chess.Board())
    assert len(engine.table) > 0


def test_engine_keeps_working_across_moves():
    # The table survives from one move to the next, and later moves still come out legal.
    board = chess.Board()
    engine = StockFihEngine(depth=2, seed=1)
    for _ in range(4):
        move = engine.choose_move(board)
        assert move in board.legal_moves
        board.push(move)


def test_engine_still_finds_mate_in_two_with_table():
    board = chess.Board(MATE_IN_TWO)
    engine = StockFihEngine(depth=3, seed=1)
    move = engine.choose_move(board)
    board.push(move)
    for reply in list(board.legal_moves):
        board.push(reply)
        assert any(
            (board.push(m), board.is_checkmate(), board.pop())[1] for m in list(board.legal_moves)
        )
        board.pop()
