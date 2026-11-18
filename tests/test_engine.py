import chess
import pytest

import stockfih.engine.stockfih as engine
from stockfih.engine.stockfih import (
    INF,
    MATE,
    StockFihEngine,
    _leaf,
    evaluate,
    material,
    negamax,
)

MATED = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"


def plain_quiescence(board: chess.Board, ply: int, qply: int = 0) -> int:
    # Reference: stand pat or play any capture, no pruning, no ordering.
    stand = _leaf(board, ply)
    if qply >= engine.QUIESCENCE_PLIES:
        return stand
    best = stand
    for move in list(board.generate_legal_captures()):
        board.push(move)
        best = max(best, -plain_quiescence(board, ply + 1, qply + 1))
        board.pop()
    return best


def plain_negamax(board: chess.Board, depth: int, ply: int = 0) -> int:
    # Reference: same scoring, no pruning, no ordering. Alpha-beta must match it exactly.
    if depth == 0:
        return plain_quiescence(board, ply)
    moves = list(board.legal_moves)
    if not moves:
        return _leaf(board, ply)
    best = -INF
    for move in moves:
        board.push(move)
        best = max(best, -plain_negamax(board, depth - 1, ply + 1))
        board.pop()
    return best


def test_start_position_is_equal():
    board = chess.Board()
    assert material(board) == 0
    assert evaluate(board) == 0


def test_evaluate_is_from_side_to_move():
    # White is up a queen.
    white_to_move = chess.Board("4k3/8/8/8/8/8/8/3QK3 w - - 0 1")
    black_to_move = chess.Board("4k3/8/8/8/8/8/8/3QK3 b - - 0 1")
    assert material(white_to_move) == 900
    assert evaluate(white_to_move) > 800  # queen plus small placement terms
    assert evaluate(black_to_move) == -evaluate(white_to_move)


def test_checkmate_and_stalemate_scores():
    assert evaluate(chess.Board(MATED)) == -MATE  # side to move is mated
    stalemate = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert evaluate(stalemate) == 0


def test_returns_legal_move_and_keeps_board():
    board = chess.Board()
    before = board.fen()
    move = StockFihEngine(seed=1).choose_move(board)
    assert move in board.legal_moves
    assert board.fen() == before
    assert len(board.move_stack) == 0


def test_takes_free_queen():
    board = chess.Board("4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1")
    assert StockFihEngine(seed=1).choose_move(board) == chess.Move.from_uci("d1d5")


def test_plays_mate_in_one():
    board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2")
    assert StockFihEngine(seed=1).choose_move(board) == chess.Move.from_uci("d8h4")


def test_no_legal_moves_raises():
    with pytest.raises(ValueError):
        StockFihEngine().choose_move(chess.Board(MATED))


def test_same_seed_same_move():
    board = chess.Board()
    assert StockFihEngine(seed=5).choose_move(board) == StockFihEngine(seed=5).choose_move(board)


def test_bad_depth_rejected():
    with pytest.raises(ValueError):
        StockFihEngine(depth=0)


@pytest.mark.parametrize(
    "fen, depth",
    [
        ("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 2 3", 2),
        ("4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1", 3),
        ("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", 2),
    ],
)
def test_alpha_beta_matches_plain_negamax(monkeypatch, fen, depth):
    monkeypatch.setattr(engine, "QUIESCENCE_PLIES", 2)  # keeps the unpruned reference fast
    board = chess.Board(fen)
    before = board.fen()
    assert negamax(board, depth, -INF, INF) == plain_negamax(board, depth)
    assert board.fen() == before


def test_finds_mate_in_two():
    # Ladder mate: 1.R(any)7 then 2.Ra8# whatever Black does.
    board = chess.Board("6k1/8/8/8/8/8/R7/1R4K1 w - - 0 1")
    move = StockFihEngine(depth=3, seed=1).choose_move(board)
    board.push(move)
    for reply in list(board.legal_moves):
        board.push(reply)
        assert any(
            (board.push(m), board.is_checkmate(), board.pop())[1] for m in list(board.legal_moves)
        )
        board.pop()


def test_prefers_faster_mate():
    # Qh4# is mate in 1; deeper search must not pick a slower mate instead.
    board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2")
    assert StockFihEngine(depth=4, seed=1).choose_move(board) == chess.Move.from_uci("d8h4")
