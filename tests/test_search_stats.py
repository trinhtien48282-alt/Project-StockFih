import time

import chess
import pytest

from stockfih.engine.stats import SearchStats, SearchTimeout
from stockfih.engine.stockfih import INF, StockFihEngine, negamax

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def test_nps_is_none_without_time():
    assert SearchStats().nps is None


def test_nps_from_nodes_and_seconds():
    assert SearchStats(nodes=500, seconds=2.0).nps == 250.0


def test_tick_counts_without_deadline():
    stats = SearchStats()
    for _ in range(1000):
        stats.tick()
    assert stats.nodes == 1000


def test_tick_raises_after_deadline():
    stats = SearchStats(deadline=time.perf_counter() - 1)
    with pytest.raises(SearchTimeout):
        for _ in range(1000):
            stats.tick()


def test_negamax_raises_on_expired_deadline():
    stats = SearchStats(deadline=time.perf_counter() - 1)
    with pytest.raises(SearchTimeout):
        negamax(chess.Board(KIWIPETE), 3, -INF, INF, 0, None, stats)


def test_negamax_counts_nodes():
    stats = SearchStats()
    negamax(chess.Board(), 2, -INF, INF, 0, None, stats)
    assert stats.nodes > 0


def test_negamax_without_stats_still_works():
    assert isinstance(negamax(chess.Board(), 2, -INF, INF), int)


def test_choose_move_fills_stats():
    engine = StockFihEngine(depth=2, seed=1)
    engine.choose_move(chess.Board())
    assert engine.stats.nodes > 0
    assert engine.stats.seconds > 0
    assert engine.stats.nps is not None and engine.stats.nps > 0
    assert engine.stats.timed_out is False
    assert engine.reached_depth == 2


def test_stats_reset_each_move():
    engine = StockFihEngine(depth=1, seed=1)
    board = chess.Board()
    engine.choose_move(board)
    first = engine.stats
    engine.choose_move(board)
    assert engine.stats is not first
    assert engine.stats.nodes == first.nodes  # depth 1, same position, same work


def test_time_limit_stops_deep_search():
    engine = StockFihEngine(depth=20, seed=1, time_limit=0.3)
    board = chess.Board(KIWIPETE)
    before = board.fen()
    start = time.perf_counter()
    move = engine.choose_move(board)
    elapsed = time.perf_counter() - start
    assert move in board.legal_moves
    assert board.fen() == before
    assert engine.stats.timed_out is True
    assert 1 <= engine.reached_depth < 20
    assert elapsed < 2.0  # generous: the limit is 0.3 s, overshoot is one 128-node slice


def test_tiny_limit_still_returns_a_legal_move():
    engine = StockFihEngine(depth=5, seed=1, time_limit=1e-9)
    board = chess.Board(KIWIPETE)
    assert engine.choose_move(board) in board.legal_moves
    assert engine.reached_depth == 1
    assert engine.stats.timed_out is True


def test_no_limit_reaches_full_depth():
    engine = StockFihEngine(depth=2, seed=1)
    engine.choose_move(chess.Board())
    assert engine.reached_depth == 2
    assert engine.stats.timed_out is False


def test_engine_works_after_a_timed_out_search():
    engine = StockFihEngine(depth=20, seed=1, time_limit=0.2)
    board = chess.Board(KIWIPETE)
    engine.choose_move(board)
    engine.time_limit = None
    engine.depth = 2
    assert engine.choose_move(board) in board.legal_moves
    assert engine.stats.timed_out is False


@pytest.mark.parametrize("bad", [0, -1, -0.5])
def test_bad_time_limit_rejected(bad):
    with pytest.raises(ValueError):
        StockFihEngine(time_limit=bad)
