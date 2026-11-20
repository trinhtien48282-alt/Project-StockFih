from dataclasses import dataclass
from time import perf_counter

import chess

from stockfih.engine.stockfih import StockFihEngine

# Tactical positions, checked by hand. Each has a rule the engine's move must satisfy, so no
# answer key is needed and a second correct move still counts:
#   "mate"      the move must give checkmate
#   "win_piece" the move must capture the piece on `target`
# Speed and accuracy on these measure tactics only. No ELO claim comes from here.
# Tests check every position is legal and that a solution exists, so a bad FEN is caught.


@dataclass(frozen=True)
class Puzzle:
    name: str
    fen: str
    kind: str  # "mate" or "win_piece"
    target: str = ""  # square name, only for "win_piece"


PUZZLES = (
    Puzzle("Back rank mate", "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "mate"),
    Puzzle("Queen mate", "k7/7Q/1K6/8/8/8/8/8 w - - 0 1", "mate"),
    Puzzle("Free queen", "4k3/8/8/3q4/8/2N5/8/4K3 w - - 0 1", "win_piece", "d5"),
)


@dataclass(frozen=True)
class PuzzleResult:
    name: str
    kind: str
    move: str  # SAN of the move the engine chose
    passed: bool
    depth: int  # depth asked for
    reached_depth: int  # deepest pass that finished
    nodes: int
    seconds: float


def _passes(board: chess.Board, move: chess.Move, puzzle: Puzzle) -> bool:
    if puzzle.kind == "mate":
        board.push(move)
        ok = board.is_checkmate()
        board.pop()
        return ok
    if puzzle.kind == "win_piece":
        return board.is_capture(move) and chess.square_name(move.to_square) == puzzle.target
    raise ValueError(f"Unknown puzzle kind: {puzzle.kind}")


def solve(puzzle: Puzzle, depth: int = 3) -> PuzzleResult:
    engine = StockFihEngine(depth=depth, seed=1)
    board = chess.Board(puzzle.fen)
    start = perf_counter()
    move = engine.choose_move(board)
    seconds = perf_counter() - start
    san = board.san(move)  # before passes() changes the board
    return PuzzleResult(
        name=puzzle.name,
        kind=puzzle.kind,
        move=san,
        passed=_passes(board, move, puzzle),
        depth=depth,
        reached_depth=engine.reached_depth,
        nodes=engine.stats.nodes,
        seconds=seconds,
    )


def run(depth: int = 3, puzzles: tuple[Puzzle, ...] = PUZZLES) -> list[PuzzleResult]:
    # A fresh engine per puzzle, so transposition-table entries cannot carry over.
    return [solve(p, depth) for p in puzzles]


def format_table(results: list[PuzzleResult]) -> str:
    header = f"{'Puzzle':<16}{'Kind':<11}{'Move':>8}{'Result':>8}{'Depth':>7}{'Reached':>8}{'Nodes':>9}{'Seconds':>9}"
    lines = [header, "-" * len(header)]
    for r in results:
        lines.append(
            f"{r.name:<16}{r.kind:<11}{r.move:>8}{'PASS' if r.passed else 'FAIL':>8}"
            f"{r.depth:>7}{r.reached_depth:>8}{r.nodes:>9}{r.seconds:>9.2f}"
        )
    passed = sum(r.passed for r in results)
    lines.append(f"\n{passed} of {len(results)} passed.")
    return "\n".join(lines)
