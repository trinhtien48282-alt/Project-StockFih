import chess
import pytest

from stockfih.engine.stats import SearchStats, SearchTimeout
from stockfih.engine.stockfih import DIFFICULTIES, StockFihEngine

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def test_tick_raises_at_node_limit():
    stats = SearchStats(node_limit=5)
    with pytest.raises(SearchTimeout):
        for _ in range(10):
            stats.tick()
    assert stats.nodes == 5


def test_node_limit_stops_deep_search():
    engine = StockFihEngine(depth=20, seed=1, node_limit=2000)
    board = chess.Board(KIWIPETE)
    before = board.fen()
    move = engine.choose_move(board)
    assert move in board.legal_moves
    assert board.fen() == before
    assert engine.stats.timed_out is True
    assert engine.stats.nodes <= 2000
    assert 1 <= engine.reached_depth < 20


def test_node_limit_is_repeatable():
    board = chess.Board(KIWIPETE)
    a = StockFihEngine(depth=20, seed=1, node_limit=1500)
    b = StockFihEngine(depth=20, seed=1, node_limit=1500)
    assert a.choose_move(board) == b.choose_move(board)
    assert a.stats.nodes == b.stats.nodes
    assert a.reached_depth == b.reached_depth


def test_tiny_node_limit_still_returns_a_legal_move():
    engine = StockFihEngine(depth=5, seed=1, node_limit=1)
    board = chess.Board(KIWIPETE)
    assert engine.choose_move(board) in board.legal_moves
    assert engine.reached_depth == 1
    assert engine.stats.timed_out is True


def test_no_node_limit_reaches_full_depth():
    engine = StockFihEngine(depth=2, seed=1)
    engine.choose_move(chess.Board())
    assert engine.reached_depth == 2
    assert engine.stats.timed_out is False


@pytest.mark.parametrize("bad", [0, -1])
def test_bad_node_limit_rejected(bad):
    with pytest.raises(ValueError):
        StockFihEngine(node_limit=bad)


@pytest.mark.parametrize("name", list(DIFFICULTIES))
def test_every_preset_applies(name):
    engine = StockFihEngine(node_limit=100)
    engine.set_difficulty(name)
    preset = DIFFICULTIES[name]
    assert (engine.depth, engine.time_limit, engine.node_limit) == (
        preset["depth"],
        preset["time_limit"],
        preset["node_limit"],
    )


def test_preset_replaces_old_limits():
    engine = StockFihEngine(time_limit=0.5, node_limit=100)
    engine.set_difficulty("Hard")
    assert engine.time_limit is None and engine.node_limit is None


def test_unknown_difficulty_changes_nothing():
    engine = StockFihEngine(depth=2, time_limit=1.0)
    with pytest.raises(ValueError):
        engine.set_difficulty("Godlike")
    assert engine.depth == 2 and engine.time_limit == 1.0


def test_easy_plays_a_legal_move_at_depth_one():
    engine = StockFihEngine(seed=1)
    engine.set_difficulty("Easy")
    board = chess.Board()
    assert engine.choose_move(board) in board.legal_moves
    assert engine.reached_depth == 1
