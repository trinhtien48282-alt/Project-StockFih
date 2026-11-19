import chess
import pytest

from stockfih.engine.stockfih import INF, StockFihEngine, negamax

SCHOLAR = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 2 3"


def best_moves(fen: str, depth: int) -> set[chess.Move]:
    # Reference: every root move searched with a full window, no iterative deepening.
    board = chess.Board(fen)
    scores = {}
    for move in list(board.legal_moves):
        board.push(move)
        scores[move] = -negamax(board, depth - 1, -INF, INF, 1)
        board.pop()
    top = max(scores.values())
    return {m for m, s in scores.items() if s == top}


@pytest.mark.parametrize("depth", [1, 2])
def test_picks_only_moves_that_are_best_at_full_depth(depth):
    expected = best_moves(SCHOLAR, depth)
    for seed in range(5):
        move = StockFihEngine(depth=depth, seed=seed).choose_move(chess.Board(SCHOLAR))
        assert move in expected


def test_reaches_requested_depth():
    engine = StockFihEngine(depth=3, seed=1)
    engine.choose_move(chess.Board())
    assert engine.reached_depth == 3


def test_stops_early_on_forced_mate():
    # Qh4# is mate in 1: no need to search to depth 5.
    board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2")
    engine = StockFihEngine(depth=5, seed=1)
    assert engine.choose_move(board) == chess.Move.from_uci("d8h4")
    assert engine.reached_depth == 1


def test_board_is_unchanged():
    board = chess.Board(SCHOLAR)
    before = board.fen()
    StockFihEngine(depth=2, seed=1).choose_move(board)
    assert board.fen() == before
    assert len(board.move_stack) == 0
