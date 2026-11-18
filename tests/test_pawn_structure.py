import chess

from stockfih.engine.pawn_structure import (
    DOUBLED_CP,
    ISOLATED_CP,
    PASSED_CP,
    pawn_structure,
)

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def test_start_position_is_even():
    assert pawn_structure(chess.Board()) == 0


def test_no_pawns_is_zero():
    assert pawn_structure(chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")) == 0


def test_mirror_flips_sign():
    board = chess.Board(KIWIPETE)
    assert pawn_structure(board) == -pawn_structure(board.mirror())


def test_isolated_pawn_costs():
    # White e4 has no neighbor. Black d7 e7 f7 are connected and sit in front of it,
    # so nobody is passed.
    board = chess.Board("4k3/3ppp2/8/8/4P3/8/8/4K3 w - - 0 1")
    assert pawn_structure(board) == -ISOLATED_CP


def test_doubled_pawn_costs():
    # White d3 d4 e4 (connected, one doubled file) against black c7 d7 e7 (all blocked).
    board = chess.Board("4k3/2ppp3/8/8/3PP3/3P4/8/4K3 w - - 0 1")
    assert pawn_structure(board) == -DOUBLED_CP


def test_passed_pawn_pays_by_rank():
    # White e5 is passed (rank index 4). Black a7 is passed too (rank index 1 for Black).
    # Both are isolated, so those cancel.
    board = chess.Board("4k3/p7/8/4P3/8/8/8/4K3 w - - 0 1")
    assert pawn_structure(board) == PASSED_CP[4] - PASSED_CP[1]


def test_enemy_pawn_ahead_on_neighbor_file_blocks():
    # Black d7 is in front of White e5 on a neighboring file, and e5 is in front of d7.
    board = chess.Board("4k3/3p4/8/4P3/8/8/8/4K3 w - - 0 1")
    assert pawn_structure(board) == 0


def test_enemy_pawn_beside_does_not_block():
    # Same rank on neighboring files: both pawns are still passed.
    board = chess.Board("4k3/8/8/3pP3/8/8/8/4K3 w - - 0 1")
    assert pawn_structure(board) == PASSED_CP[4] - PASSED_CP[3]
