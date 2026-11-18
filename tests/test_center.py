import chess

from stockfih.engine.center import ATTACK_CP, center_control

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def test_start_position_is_even():
    assert center_control(chess.Board()) == 0


def test_mirror_flips_sign():
    board = chess.Board(KIWIPETE)
    assert center_control(board) == -center_control(board.mirror())


def test_knight_hits_two_center_squares():
    # Nf3 attacks d4 and e5.
    board = chess.Board("4k3/8/8/8/8/5N2/8/4K3 w - - 0 1")
    assert center_control(board) == 2 * ATTACK_CP


def test_pawn_hits_one_center_square():
    # Pawn d3 attacks c4 and e4. Only e4 is central.
    board = chess.Board("4k3/8/8/8/8/3P4/8/4K3 w - - 0 1")
    assert center_control(board) == ATTACK_CP


def test_board_is_unchanged():
    board = chess.Board(KIWIPETE)
    before = board.fen()
    center_control(board)
    assert board.fen() == before
