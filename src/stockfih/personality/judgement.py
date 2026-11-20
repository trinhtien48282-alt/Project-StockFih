import chess

from stockfih.personality.events import EventKind, GameEvent, check_move

# Judges a move from two numbers an engine measured. This module never imports the engine:
# the caller searches the position and passes the scores in. Without both scores nothing is
# judged, so no judgement can be claimed without an evaluation behind it.
#
# Both scores are centipawns from the point of view of the side that moved:
#   best    the score of the best move in the position before the move
#   played  the score of the position after the move actually played
# The same engine at the same depth should produce both. The thresholds are plain design
# numbers to tune later, not official chess categories.
INACCURACY_CP = 50  # losing at least this much is an inaccuracy
MISTAKE_CP = 100
BLUNDER_CP = 200
WINNING_CP = 300  # at or above this a side is "clearly winning"; at or below minus this, losing
MATE_BOUND = 99_000  # scores beyond this mean a forced mate. A test keeps it equal to the engine's.
# shortcut: BRILLIANT is not defined. It needs a sacrifice detector, so it cannot be claimed yet.


def judge(best: int, played: int) -> EventKind | None:
    # None means the move is fine, or nothing useful can be said about it.
    # Walked into a forced mate from a position that was not already lost.
    if played <= -MATE_BOUND and best > -WINNING_CP:
        return EventKind.BLUNDER
    # Had a forced mate and no longer does.
    if best >= MATE_BOUND and played < MATE_BOUND:
        return EventKind.MISSED_WIN
    # Both scores on the same decisive side: the move did not change who is winning, so there
    # is nobody to blame (a lost position stays lost, a won one stays won).
    if (best >= WINNING_CP and played >= WINNING_CP) or (best <= -WINNING_CP and played <= -WINNING_CP):
        return None
    loss = max(0, best - played)  # depth noise can make `played` look better: that is not a loss
    if best >= WINNING_CP and played < WINNING_CP and played > -WINNING_CP and loss >= MISTAKE_CP:
        return EventKind.MISSED_WIN  # a win thrown away, but the game is not lost yet
    if loss >= BLUNDER_CP:
        return EventKind.BLUNDER
    if loss >= MISTAKE_CP:
        return EventKind.MISTAKE
    if loss >= INACCURACY_CP:
        return EventKind.INACCURACY
    return None


def judgement_event(
    board: chess.Board, move: chess.Move, by: str, best: int, played: int
) -> GameEvent | None:
    # `board` is the position BEFORE the move and is left unchanged. Returns the judgement as
    # an event, or None when `judge` has nothing to say. ValueError for an illegal move or
    # an unknown `by`.
    check_move(board, move, by)
    kind = judge(best, played)
    if kind is None:
        return None
    mate = abs(best) >= MATE_BOUND or abs(played) >= MATE_BOUND
    return GameEvent(
        kind,
        by,
        board.ply() + 1,
        board.san(move),
        board.turn,
        loss=None if mate else max(0, best - played),
    )
