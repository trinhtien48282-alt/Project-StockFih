import random
import struct

import chess
import chess.polyglot
import pytest

from stockfih.engine.book import OpeningBook
from stockfih.engine.stockfih import StockFihEngine

E2E4 = chess.Move.from_uci("e2e4")
D2D4 = chess.Move.from_uci("d2d4")
E2E5 = chess.Move.from_uci("e2e5")  # illegal from the start position


def write_book(path, entries):
    # entries: (board, move, weight). Polyglot record: key u64, move u16, weight u16, learn u32,
    # big-endian, sorted by key. Move bits: to | from << 6 | promotion << 12.
    rows = []
    for board, move, weight in entries:
        raw = move.to_square | (move.from_square << 6) | ((move.promotion or 0) << 12)
        rows.append((chess.polyglot.zobrist_hash(board), raw, weight, 0))
    rows.sort()
    path.write_bytes(b"".join(struct.pack(">QHHI", *row) for row in rows))
    return path


def test_missing_file_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        OpeningBook(tmp_path / "nope.bin")


def test_pick_returns_a_book_move(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E4, 10), (chess.Board(), D2D4, 5)]))
    for seed in range(20):
        assert book.pick(chess.Board(), random.Random(seed)) in (E2E4, D2D4)


def test_single_entry_is_always_chosen(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), D2D4, 1)]))
    assert all(book.pick(chess.Board(), random.Random(s)) == D2D4 for s in range(10))


def test_weights_are_used(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E4, 1000), (chess.Board(), D2D4, 1)]))
    rng = random.Random(0)
    picks = [book.pick(chess.Board(), rng) for _ in range(100)]
    assert picks.count(E2E4) > 80


def test_all_zero_weights_still_pick(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E4, 0), (chess.Board(), D2D4, 0)]))
    assert book.pick(chess.Board(), random.Random(0)) in (E2E4, D2D4)


def test_position_not_in_book(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E4, 1)]))
    other = chess.Board()
    other.push_san("a3")
    assert book.pick(other, random.Random(0)) is None


def test_illegal_entry_is_ignored(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E5, 1)]))
    assert book.pick(chess.Board(), random.Random(0)) is None


def test_empty_file_is_not_a_crash(tmp_path):
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")
    assert OpeningBook(path).pick(chess.Board(), random.Random(0)) is None


def test_pick_leaves_board_alone(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E4, 1)]))
    board = chess.Board()
    book.pick(board, random.Random(0))
    assert board.fen() == chess.STARTING_FEN and not board.move_stack


def test_engine_plays_book_move_without_search(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E4, 1)]))
    engine = StockFihEngine(depth=3, seed=1, book=book)
    assert engine.choose_move(chess.Board()) == E2E4
    assert engine.from_book is True
    assert engine.stats.nodes == 0
    assert engine.reached_depth == 0


def test_engine_searches_when_not_in_book(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E4, 1)]))
    engine = StockFihEngine(depth=1, seed=1, book=book)
    board = chess.Board()
    board.push_san("a3")
    assert engine.choose_move(board) in board.legal_moves
    assert engine.from_book is False
    assert engine.stats.nodes > 0


def test_from_book_resets_each_move(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E4, 1)]))
    engine = StockFihEngine(depth=1, seed=1, book=book)
    engine.choose_move(chess.Board())
    board = chess.Board()
    board.push_san("a3")
    engine.choose_move(board)
    assert engine.from_book is False


def test_engine_without_book_unchanged():
    engine = StockFihEngine(depth=1, seed=1)
    engine.choose_move(chess.Board())
    assert engine.from_book is False


def test_game_over_still_raises_with_book(tmp_path):
    book = OpeningBook(write_book(tmp_path / "b.bin", [(chess.Board(), E2E4, 1)]))
    mated = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    with pytest.raises(ValueError):
        StockFihEngine(book=book).choose_move(mated)
