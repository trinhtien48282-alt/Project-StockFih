import chess
import pytest

from stockfih.engine.stockfih import MATE, StockFihEngine, evaluate, material


def test_start_position_is_equal():
    board = chess.Board()
    assert material(board) == 0
    assert evaluate(board) == 0


def test_evaluate_is_from_side_to_move():
    # White is up a queen.
    white_to_move = chess.Board("4k3/8/8/8/8/8/8/3QK3 w - - 0 1")
    black_to_move = chess.Board("4k3/8/8/8/8/8/8/3QK3 b - - 0 1")
    assert evaluate(white_to_move) == 900
    assert evaluate(black_to_move) == -900


def test_checkmate_and_stalemate_scores():
    mated = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    assert evaluate(mated) == -MATE  # side to move is mated
    stalemate = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert evaluate(stalemate) == 0


def test_returns_legal_move_and_keeps_board():
    board = chess.Board()
    before = board.fen()
    move = StockFihEngine(seed=1).choose_move(board)
    assert move in board.legal_moves
    assert board.fen() == before


def test_takes_free_queen():
    board = chess.Board("4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1")
    assert StockFihEngine(seed=1).choose_move(board) == chess.Move.from_uci("d1d5")


def test_plays_mate_in_one():
    board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2")
    assert StockFihEngine(seed=1).choose_move(board) == chess.Move.from_uci("d8h4")


def test_no_legal_moves_raises():
    board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    with pytest.raises(ValueError):
        StockFihEngine().choose_move(board)


def test_same_seed_same_move():
    board = chess.Board()
    assert StockFihEngine(seed=5).choose_move(board) == StockFihEngine(seed=5).choose_move(board)
