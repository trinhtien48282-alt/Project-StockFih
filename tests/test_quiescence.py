import chess

from stockfih.engine.stockfih import INF, StockFihEngine, _leaf, quiescence


def test_quiet_position_returns_static_score():
    board = chess.Board()  # no captures available
    assert quiescence(board, -INF, INF, 0) == _leaf(board, 0)


def test_free_piece_is_counted():
    # White to move can take an undefended queen: quiescence must see the gain.
    board = chess.Board("4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1")
    assert quiescence(board, -INF, INF, 0) >= _leaf(board, 0) + 800


def test_defended_pawn_is_not_free():
    # Qxd5 would win a pawn on the surface, but c6 recaptures the queen.
    board = chess.Board("4k3/8/2p5/3p4/8/8/3Q4/4K3 w - - 0 1")
    assert StockFihEngine(depth=1, seed=1).choose_move(board) != chess.Move.from_uci("d2d5")


def test_board_is_unchanged():
    board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 2 3")
    before = board.fen()
    quiescence(board, -INF, INF, 0)
    assert board.fen() == before
    assert len(board.move_stack) == 0
