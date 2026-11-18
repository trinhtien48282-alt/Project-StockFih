import chess

from stockfih.engine.mobility import MOVE_CP, mobility

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def test_start_position_is_even():
    assert mobility(chess.Board()) == 0


def test_mirror_flips_sign():
    board = chess.Board(KIWIPETE)
    assert mobility(board) == -mobility(board.mirror())


def test_board_is_unchanged():
    board = chess.Board(KIWIPETE)
    before = board.fen()
    mobility(board)
    assert board.fen() == before
    assert board.turn == chess.WHITE


def test_lone_rook_counts_its_moves():
    # White: king e1 has 5 moves, rook h1 has 9 (g1, f1, h2 to h8). Black king e8 has 5.
    board = chess.Board("4k3/8/8/8/8/8/8/4K2R w - - 0 1")
    assert mobility(board) == MOVE_CP * (14 - 5)
