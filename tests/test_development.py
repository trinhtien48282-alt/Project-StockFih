import chess

from stockfih.engine.development import EARLY_QUEEN_CP, HOME_CP, development

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def test_start_position_is_even():
    assert development(chess.Board()) == 0


def test_mirror_flips_sign():
    board = chess.Board(KIWIPETE)
    assert development(board) == -development(board.mirror())


def test_developing_a_knight_pays():
    # After 1.Nf3: White has 3 pieces at home, Black has 4.
    board = chess.Board("rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1")
    assert development(board) == HOME_CP


def test_early_queen_move_costs():
    # After 1.e4 e5 2.Qh5: both sides have 4 pieces at home, White's queen has left d1.
    board = chess.Board("rnbqkbnr/pppp1ppp/8/4p2Q/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 1 2")
    assert development(board) == -EARLY_QUEEN_CP


def test_queen_move_is_fine_once_developed():
    # White has only Bc1 at home, so the queen on g1 is not penalized.
    board = chess.Board("3qk3/8/8/8/8/2N2N2/8/2B1K1Q1 w - - 0 1")
    assert development(board) == -HOME_CP


def test_zero_without_queens():
    board = chess.Board("4k3/8/8/8/8/8/8/1N2K1N1 w - - 0 1")
    assert development(board) == 0
