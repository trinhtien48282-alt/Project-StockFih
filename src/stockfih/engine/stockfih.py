import random

import chess

from stockfih.engine.pst import positional

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
INF = 10**9
DEFAULT_DEPTH = 3  # plies. Python is slow: 4+ can take many seconds in busy positions.


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
    score = material(board) + positional(board)
    return score if board.turn == chess.WHITE else -score


def _leaf(board: chess.Board, ply: int) -> int:
    # Static score at the end of a line. Being mated `ply` moves from the root scores
    # -MATE + ply, so the engine prefers the quickest mate and delays being mated.
    score = evaluate(board)
    return score + ply if score == -MATE else score


def _order_key(board: chess.Board, move: chess.Move) -> int:
    # Better moves first, so alpha-beta cuts sooner. Captures: most valuable victim, least
    # valuable attacker (MVV-LVA). Promotions next. Quiet moves last.
    score = 0
    if board.is_capture(move):
        victim = board.piece_type_at(move.to_square) or chess.PAWN  # en passant: square is empty
        attacker = board.piece_type_at(move.from_square)
        score = 1000 + 10 * VALUES[victim] - VALUES[attacker]
    if move.promotion:
        score += VALUES[move.promotion]
    return score


def _ordered(board: chess.Board, moves: list[chess.Move]) -> list[chess.Move]:
    return sorted(moves, key=lambda m: _order_key(board, m), reverse=True)


def negamax(board: chess.Board, depth: int, alpha: int, beta: int, ply: int = 0) -> int:
    # Alpha-beta negamax. Score for the side to move, searching `depth` more plies.
    # Pushes and pops moves on `board`, so it ends up unchanged.
    # shortcut: no repetition or 50-move draws inside the search, and no quiescence, so it
    # can misjudge captures at the horizon. 8.1 adds quiescence.
    if depth == 0:
        return _leaf(board, ply)
    moves = list(board.legal_moves)
    if not moves:
        return _leaf(board, ply)  # checkmate or stalemate
    best = -INF
    for move in _ordered(board, moves):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, ply + 1)
        board.pop()
        best = max(best, score)
        alpha = max(alpha, best)
        if alpha >= beta:
            break
    return best


class StockFihEngine:
    def __init__(self, depth: int = DEFAULT_DEPTH, seed: int | None = None) -> None:
        if depth < 1:
            raise ValueError("Search depth must be at least 1.")
        self.depth = depth  # plies, can be changed between moves
        self._rng = random.Random(seed)  # a seed makes tie-breaks repeatable (tests)

    def choose_move(self, board: chess.Board) -> chess.Move:
        moves = list(board.legal_moves)
        if not moves:
            raise ValueError("No legal moves: the game is over.")
        work = board.copy()  # never touch the caller's board
        best_score = -INF
        best: list[chess.Move] = []
        for move in _ordered(work, moves):
            work.push(move)
            # Window starts one below the best score so equal moves still return an exact
            # score (needed for random tie-breaks); worse moves fail low and are cut early.
            score = -negamax(work, self.depth - 1, -INF, -(best_score - 1), 1)
            work.pop()
            if score > best_score:
                best_score, best = score, [move]
            elif score == best_score:
                best.append(move)
        return self._rng.choice(best)  # equal moves: pick one at random so games vary
