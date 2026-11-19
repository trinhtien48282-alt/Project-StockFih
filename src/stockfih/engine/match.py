from collections.abc import Callable
from dataclasses import dataclass

import chess

from stockfih.engine.base import Engine

# Short fixed openings (SAN), so games differ. Every opening is played twice with colours
# swapped, so neither engine gets the better side. No ELO comes from this: a few games
# only show which engine scored more, and that is noisy.
OPENINGS = (
    ("e4", "e5", "Nf3", "Nc6"),
    ("d4", "d5", "c4", "e6"),
    ("c4", "e5", "Nc3", "Nf6"),
    ("e4", "c5", "Nf3", "d6"),
)
MAX_PLIES = 200  # plies played by the engines per game; a longer game is stopped as a draw


@dataclass(frozen=True)
class GameResult:
    opening: int  # index into the openings used
    a_is_white: bool
    result: str  # "1-0", "0-1" or "1/2-1/2", from White's point of view
    plies: int  # plies the engines played (the opening moves are not counted)
    adjudicated: bool  # True when the ply cap stopped the game; scored as a draw

    @property
    def a_score(self) -> float:
        # 1 win, 0.5 draw, 0 loss, for engine A.
        if self.result == "1/2-1/2":
            return 0.5
        return 1.0 if (self.result == "1-0") == self.a_is_white else 0.0


@dataclass(frozen=True)
class MatchSummary:
    wins: int  # of engine A
    draws: int
    losses: int
    adjudicated: int  # games stopped by the ply cap (already counted as draws above)

    @property
    def games(self) -> int:
        return self.wins + self.draws + self.losses

    @property
    def score(self) -> float | None:
        # A's points over games played. None until there is a game.
        return (self.wins + 0.5 * self.draws) / self.games if self.games else None


def summarize(results: list[GameResult]) -> MatchSummary:
    scores = [g.a_score for g in results]
    return MatchSummary(
        wins=scores.count(1.0),
        draws=scores.count(0.5),
        losses=scores.count(0.0),
        adjudicated=sum(g.adjudicated for g in results),
    )


def play_game(
    white: Engine, black: Engine, start: chess.Board, max_plies: int = MAX_PLIES
) -> tuple[str, int, bool]:
    # Returns (result, plies played, stopped by the ply cap). `start` is left unchanged.
    # Threefold and 50-move draws are applied when claimable. The engines themselves ignore
    # move history (see negamax), so they can shuffle into a repetition; this ends it.
    # Raises ValueError if an engine returns an illegal move: that is an engine bug.
    board = start.copy()
    plies = 0
    while True:
        out = board.outcome(claim_draw=True)
        if out is not None:
            return out.result(), plies, False
        if plies >= max_plies:
            return "1/2-1/2", plies, True
        engine = white if board.turn == chess.WHITE else black
        move = engine.choose_move(board)
        if move not in board.legal_moves:
            raise ValueError(f"Engine played an illegal move {move.uci()} in {board.fen()}")
        board.push(move)
        plies += 1


def _opening_board(line: tuple[str, ...]) -> chess.Board:
    board = chess.Board()
    for san in line:
        board.push_san(san)
    return board


def play_match(
    make_a: Callable[[], Engine],
    make_b: Callable[[], Engine],
    openings: tuple[tuple[str, ...], ...] = OPENINGS,
    max_plies: int = MAX_PLIES,
    on_game: Callable[[GameResult], None] | None = None,
) -> list[GameResult]:
    # Each opening twice: A as White, then A as Black. Fresh engines per game, so a
    # transposition table from one game cannot carry into the next.
    results = []
    for index, line in enumerate(openings):
        start = _opening_board(line)
        for a_is_white in (True, False):
            a, b = make_a(), make_b()
            white, black = (a, b) if a_is_white else (b, a)
            result, plies, adjudicated = play_game(white, black, start, max_plies)
            game = GameResult(index, a_is_white, result, plies, adjudicated)
            results.append(game)
            if on_game is not None:
                on_game(game)
    return results
