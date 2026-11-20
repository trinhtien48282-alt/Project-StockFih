import chess
import pytest

from stockfih.engine.puzzles import PUZZLES, Puzzle, _passes, format_table, run, solve


@pytest.mark.parametrize("puzzle", PUZZLES, ids=lambda p: p.name)
def test_position_is_legal_and_playable(puzzle):
    board = chess.Board(puzzle.fen)
    assert board.is_valid()
    assert not board.is_game_over()


@pytest.mark.parametrize("puzzle", [p for p in PUZZLES if p.kind == "mate"], ids=lambda p: p.name)
def test_mate_puzzle_has_a_mating_move(puzzle):
    board = chess.Board(puzzle.fen)
    mates = []
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            mates.append(move)
        board.pop()
    assert mates


@pytest.mark.parametrize("puzzle", [p for p in PUZZLES if p.kind == "win_piece"], ids=lambda p: p.name)
def test_win_puzzle_target_is_capturable_queen(puzzle):
    board = chess.Board(puzzle.fen)
    square = chess.parse_square(puzzle.target)
    assert board.piece_at(square) == chess.Piece(chess.QUEEN, chess.BLACK)
    assert any(m.to_square == square and board.is_capture(m) for m in board.legal_moves)


def test_wrong_move_fails_a_mate_puzzle():
    puzzle = Puzzle("Back rank mate", "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "mate")
    board = chess.Board(puzzle.fen)
    assert _passes(board, chess.Move.from_uci("g1g2"), puzzle) is False


def test_quiet_move_fails_a_win_puzzle():
    puzzle = Puzzle("Free queen", "4k3/8/8/3q4/8/2N5/8/4K3 w - - 0 1", "win_piece", "d5")
    board = chess.Board(puzzle.fen)
    assert _passes(board, chess.Move.from_uci("e1d1"), puzzle) is False


def test_unknown_kind_raises():
    puzzle = Puzzle("x", chess.STARTING_FEN, "bogus")
    with pytest.raises(ValueError):
        _passes(chess.Board(), chess.Move.from_uci("e2e4"), puzzle)


def test_solve_keeps_board_unchanged_for_mate_check():
    result = solve(PUZZLES[0], depth=1)
    assert result.move.endswith("#")
    assert result.passed is True


def test_run_returns_one_result_per_puzzle():
    results = run(depth=1)
    assert [r.name for r in results] == [p.name for p in PUZZLES]


def test_all_puzzles_solved_at_depth_two():
    results = run(depth=2)
    failed = [r.name for r in results if not r.passed]
    assert failed == []


def test_table_reports_count():
    text = format_table(run(depth=1))
    assert f"of {len(PUZZLES)} passed" in text
