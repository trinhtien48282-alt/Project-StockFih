import random
import time

import chess
import chess.polyglot

from stockfih.engine.center import center_control
from stockfih.engine.development import development
from stockfih.engine.king_safety import king_safety
from stockfih.engine.mobility import mobility
from stockfih.engine.pawn_structure import pawn_structure
from stockfih.engine.pst import positional
from stockfih.engine.stats import SearchStats, SearchTimeout

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
QUIESCENCE_PLIES = 6  # most capture plies searched past the horizon. Bounds the worst case.
TT_MAX = 200_000  # transposition table entries kept before it is emptied (about 30 MB)
MATE_BOUND = MATE - 1000  # scores beyond this are "mate in N", not material
EXACT, LOWER, UPPER = 0, 1, 2  # what a table score means: the value, or a bound on it


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
    score = (
        material(board)
        + positional(board)
        + mobility(board)
        + king_safety(board)
        + pawn_structure(board)
        + center_control(board)
        + development(board)
    )
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


def quiescence(
    board: chess.Board,
    alpha: int,
    beta: int,
    ply: int,
    qply: int = 0,
    stats: SearchStats | None = None,
) -> int:
    # Past the horizon, keep playing captures until the position is quiet, so a capture that
    # is simply recaptured is not scored as a free win. The side to move may also "stand pat":
    # decline every capture and take the static score.
    # shortcut: captures only (no promotions, no check evasions), so a side in check still
    # stands pat. Pushes and pops moves on `board`, so it ends up unchanged
    # (except when `stats` raises SearchTimeout: then the board is left mid-line, discard it).
    if stats is not None:
        stats.tick()
    stand = _leaf(board, ply)
    if qply >= QUIESCENCE_PLIES or stand >= beta:
        return stand
    best = stand
    alpha = max(alpha, stand)
    for move in _ordered(board, list(board.generate_legal_captures())):
        board.push(move)
        score = -quiescence(board, -beta, -alpha, ply + 1, qply + 1, stats)
        board.pop()
        best = max(best, score)
        alpha = max(alpha, best)
        if alpha >= beta:
            break
    return best


def _to_table(score: int, ply: int) -> int:
    # Mate scores count plies from the root. The table must not, because the same position
    # can be reached at a different ply, so store the distance from this node instead.
    if score >= MATE_BOUND:
        return score + ply
    if score <= -MATE_BOUND:
        return score - ply
    return score


def _from_table(score: int, ply: int) -> int:
    if score >= MATE_BOUND:
        return score - ply
    if score <= -MATE_BOUND:
        return score + ply
    return score


def negamax(
    board: chess.Board,
    depth: int,
    alpha: int,
    beta: int,
    ply: int = 0,
    tt: dict | None = None,
    stats: SearchStats | None = None,
) -> int:
    # Alpha-beta negamax. Score for the side to move, searching `depth` more plies, then
    # quiescence. Pushes and pops moves on `board`, so it ends up unchanged.
    # `tt` is an optional transposition table: position hash -> (depth, kind, score, best move).
    # It skips positions already searched at least this deep and tries its best move first.
    # `stats` is optional: it counts nodes and raises SearchTimeout at its deadline. A node cut
    # off by the timeout writes nothing to `tt`, so the table only ever holds finished searches.
    # On SearchTimeout the board is left mid-line: the caller must discard it.
    # shortcut: no repetition or 50-move draws inside the search (so the table is safe to share).
    if depth == 0:
        return quiescence(board, alpha, beta, ply, 0, stats)
    if stats is not None:
        stats.tick()
    alpha0 = alpha
    key = None
    tt_move = None
    if tt is not None:
        key = chess.polyglot.zobrist_hash(board)  # standard Zobrist hash from python-chess
        entry = tt.get(key)
        if entry is not None:
            entry_depth, kind, entry_score, tt_move = entry
            if entry_depth >= depth:
                entry_score = _from_table(entry_score, ply)
                if kind == EXACT:
                    return entry_score
                if kind == LOWER:
                    alpha = max(alpha, entry_score)
                else:
                    beta = min(beta, entry_score)
                if alpha >= beta:
                    return entry_score
    moves = list(board.legal_moves)
    if not moves:
        return _leaf(board, ply)  # checkmate or stalemate
    ordered = _ordered(board, moves)
    if tt_move in ordered:  # stored move first (it can be stale after a hash collision)
        ordered.remove(tt_move)
        ordered.insert(0, tt_move)
    best = -INF
    best_move = None
    for move in ordered:
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, ply + 1, tt, stats)
        board.pop()
        if score > best:
            best, best_move = score, move
        alpha = max(alpha, best)
        if alpha >= beta:
            break
    if tt is not None:
        kind = UPPER if best <= alpha0 else LOWER if best >= beta else EXACT
        old = tt.get(key)
        if old is None or depth >= old[0]:
            tt[key] = (depth, kind, _to_table(best, ply), tt_move if kind == UPPER else best_move)
    return best


class StockFihEngine:
    def __init__(
        self, depth: int = DEFAULT_DEPTH, seed: int | None = None, time_limit: float | None = None
    ) -> None:
        if depth < 1:
            raise ValueError("Search depth must be at least 1.")
        if time_limit is not None and time_limit <= 0:
            raise ValueError("Time limit must be positive.")
        self.depth = depth  # plies, can be changed between moves
        # Seconds per move, or None for no limit. Can be changed between moves. Depth stays a
        # cap too: the search stops at whichever comes first. Depth 1 always finishes, so the
        # engine always has a move; the limit stops the deeper passes.
        self.time_limit = time_limit
        self.reached_depth = 0  # last depth fully searched by choose_move
        self.stats = SearchStats()  # numbers of the last choose_move
        self.table: dict = {}  # transposition table, kept between moves (see negamax)
        self._rng = random.Random(seed)  # a seed makes tie-breaks repeatable (tests)

    def _search_root(
        self, work: chess.Board, moves: list[chess.Move], depth: int
    ) -> tuple[dict[chess.Move, int], list[chess.Move]]:
        # Scores every root move. Returns (score per move, the moves tied for best).
        # Scores of moves that lose to the best are only upper bounds, which is enough to rank them.
        # Raises SearchTimeout when self.stats runs out of time; `work` is then mid-line.
        best_score = -INF
        best: list[chess.Move] = []
        scores: dict[chess.Move, int] = {}
        for move in moves:
            work.push(move)
            # Window starts one below the best score so equal moves still return an exact
            # score (needed for random tie-breaks); worse moves fail low and are cut early.
            score = -negamax(work, depth - 1, -INF, -(best_score - 1), 1, self.table, self.stats)
            work.pop()
            scores[move] = score
            if score > best_score:
                best_score, best = score, [move]
            elif score == best_score:
                best.append(move)
        return scores, best

    def choose_move(self, board: chess.Board) -> chess.Move:
        moves = list(board.legal_moves)
        if not moves:
            raise ValueError("No legal moves: the game is over.")
        work = board.copy()  # never touch the caller's board
        if len(self.table) > TT_MAX:
            self.table.clear()
        moves = _ordered(work, moves)
        best: list[chess.Move] = []
        start = time.perf_counter()
        end = None if self.time_limit is None else start + self.time_limit
        self.stats = stats = SearchStats()
        # Iterative deepening: search 1 ply, then 2, ... up to self.depth. Each pass starts
        # with the moves the previous pass liked best, so alpha-beta cuts more.
        # shortcut: a pass cut off by the time limit is thrown away whole, even if it had
        # already found a better move. Upgrade if the lost time matters.
        for depth in range(1, self.depth + 1):
            if depth > 1 and end is not None:  # depth 1 is never limited: a move must exist
                if time.perf_counter() >= end:
                    stats.timed_out = True
                    break
                stats.deadline = end
            try:
                scores, found = self._search_root(work, moves, depth)
            except SearchTimeout:
                stats.timed_out = True
                break
            best = found
            self.reached_depth = depth
            if scores[best[0]] >= MATE_BOUND:
                break  # forced mate found; the shallowest pass finds the quickest one
            moves = sorted(moves, key=lambda m: scores[m], reverse=True)  # stable
        stats.seconds = time.perf_counter() - start
        return self._rng.choice(best)  # equal moves: pick one at random so games vary
