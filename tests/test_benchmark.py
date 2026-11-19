import chess
import pytest

from stockfih.engine.benchmark import POSITIONS, format_table, run


def test_one_result_per_position():
    results = run(depth=1)
    assert [r.name for r in results] == [name for name, _ in POSITIONS]
    assert all(r.depth == 1 and r.reached_depth == 1 for r in results)


def test_moves_are_legal_and_nodes_counted():
    for result, (_, fen) in zip(run(depth=1), POSITIONS):
        board = chess.Board(fen)
        assert board.parse_san(result.move) in board.legal_moves
        assert result.nodes > 0
        assert result.timed_out is False


def test_table_lists_every_position():
    text = format_table(run(depth=1))
    for name, _ in POSITIONS:
        assert name in text


def test_depth_zero_rejected():
    with pytest.raises(ValueError):
        run(depth=0)
