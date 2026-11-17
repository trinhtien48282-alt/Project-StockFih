import chess
import pytest

from stockfih.engine import pst
from stockfih.engine.pst import positional

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


@pytest.mark.parametrize(
    "table",
    [pst.PAWN, pst.KNIGHT, pst.BISHOP, pst.ROOK, pst.QUEEN, pst.KING_MIDDLEGAME, pst.KING_ENDGAME],
)
def test_tables_have_64_entries(table):
    assert len(table) == 64


def test_start_position_is_zero():
    assert positional(chess.Board()) == 0


@pytest.mark.parametrize("fen", [KIWIPETE, "4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1"])
def test_color_symmetry(fen):
    board = chess.Board(fen)
    assert positional(board) == -positional(board.mirror())


def test_knight_prefers_center():
    center = chess.Board("4k3/8/8/8/4N3/8/8/4K3 w - - 0 1")
    corner = chess.Board("4k3/8/8/8/8/8/8/N3K3 w - - 0 1")
    assert positional(center) > positional(corner)


def test_pawn_e4_beats_e2():
    advanced = chess.Board("4k3/8/8/8/4P3/8/8/4K3 w - - 0 1")
    home = chess.Board("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
    assert positional(advanced) - positional(home) == 40  # +20 vs -20


def test_king_hides_with_queens_on():
    castled = chess.Board("3qk3/8/8/8/8/8/8/3Q2K1 w - - 0 1")
    center = chess.Board("3qk3/8/8/8/8/8/8/3QK3 w - - 0 1")
    assert positional(castled) > positional(center)


def test_king_centralizes_without_queens():
    center = chess.Board("4k3/8/8/8/4K3/8/8/8 w - - 0 1")
    home = chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    assert positional(center) > positional(home)
