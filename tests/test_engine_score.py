import chess

from stockfih.engine.stockfih import MATE_BOUND, StockFihEngine


class OneMoveBook:
    def pick(self, board, rng):
        return chess.Move.from_uci("e2e4")


def test_score_is_none_before_any_search():
    assert StockFihEngine().score is None


def test_score_is_an_int_after_a_search():
    engine = StockFihEngine(depth=1, seed=1)
    engine.choose_move(chess.Board())
    assert isinstance(engine.score, int)
    assert abs(engine.score) < MATE_BOUND


def test_forced_mate_scores_beyond_the_mate_bound():
    engine = StockFihEngine(depth=1, seed=1)
    engine.choose_move(chess.Board("k7/7Q/1K6/8/8/8/8/8 w - - 0 1"))
    assert engine.score >= MATE_BOUND


def test_score_is_from_the_mover_point_of_view():
    # White has an extra queen. Good for White when White moves, bad for Black when Black moves.
    white = StockFihEngine(depth=1, seed=1)
    white.choose_move(chess.Board("4k3/8/8/8/8/8/8/3QK3 w - - 0 1"))
    black = StockFihEngine(depth=1, seed=1)
    black.choose_move(chess.Board("4k3/8/8/8/8/8/8/3QK3 b - - 0 1"))
    assert white.score > 800
    assert black.score < -800


def test_book_move_has_no_score_and_resets_it():
    engine = StockFihEngine(depth=1, seed=1)
    engine.choose_move(chess.Board())
    assert engine.score is not None
    engine.book = OneMoveBook()
    engine.choose_move(chess.Board())
    assert engine.from_book is True
    assert engine.score is None
