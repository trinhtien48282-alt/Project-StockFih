import chess

from stockfih.engine.king_safety import SHIELD_CP, king_safety

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def test_start_position_is_even():
    assert king_safety(chess.Board()) == 0


def test_mirror_flips_sign():
    board = chess.Board(KIWIPETE)
    assert king_safety(board) == -king_safety(board.mirror())


def test_full_shield_beats_no_shield():
    shielded = chess.Board("3qk3/8/8/8/8/8/5PPP/3Q2K1 w - - 0 1")
    bare = chess.Board("3qk3/8/8/8/8/8/8/3Q2K1 w - - 0 1")
    assert king_safety(shielded) == 3 * SHIELD_CP
    assert king_safety(bare) == 0


def test_pawn_two_ranks_ahead_counts():
    board = chess.Board("3qk3/8/8/8/8/6P1/8/3Q2K1 w - - 0 1")
    assert king_safety(board) == SHIELD_CP


def test_pawn_beside_king_does_not_count():
    board = chess.Board("3qk3/8/8/8/8/8/6KP/3Q4 w - - 0 1")
    assert king_safety(board) == 0


def test_zero_without_queens():
    board = chess.Board("4k3/8/8/8/8/8/PPP5/3K4 w - - 0 1")
    assert king_safety(board) == 0


def test_king_on_last_rank_does_not_crash():
    board = chess.Board("K2q4/8/8/8/8/8/8/3Q1k2 w - - 0 1")
    assert isinstance(king_safety(board), int)
