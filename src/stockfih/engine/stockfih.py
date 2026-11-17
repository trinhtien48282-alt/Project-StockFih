import random

import chess

# Centipawns. The king has no material value: it can never be captured, mate is scored separately.
VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}
MATE = 100_000  # bigger than any material total, so a mate always beats winning material


def material(board: chess.Board) -> int:
    # White minus Black, in centipawns.
    return sum(
        value * (len(board.pieces(piece, chess.WHITE)) - len(board.pieces(piece, chess.BLACK)))
        for piece, value in VALUES.items()
    )


def evaluate(board: chess.Board) -> int:
    # Score from the point of view of the side to move: positive is good for them.
    out = board.outcome()
    if out is not None:
        if out.winner is None:
            return 0  # stalemate, insufficient material, 75-move, fivefold
        return MATE if out.winner == board.turn else -MATE
    score = material(board)
    return score if board.turn == chess.WHITE else -score


class StockFihEngine:
    # shortcut: looks one move ahead only (no search). 7.2 replaces this with minimax / alpha-beta.
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)  # a seed makes tie-breaks repeatable (tests)

    def choose_move(self, board: chess.Board) -> chess.Move:
        moves = list(board.legal_moves)
        if not moves:
            raise ValueError("No legal moves: the game is over.")
        work = board.copy()  # never touch the caller's board
        best_score = None
        best: list[chess.Move] = []
        for move in moves:
            work.push(move)
            score = -evaluate(work)  # evaluate() is for the opponent now, so flip it
            work.pop()
            if best_score is None or score > best_score:
                best_score, best = score, [move]
            elif score == best_score:
                best.append(move)
        return self._rng.choice(best)  # equal moves: pick one at random so games vary
