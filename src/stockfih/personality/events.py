from dataclasses import dataclass
from enum import Enum

import chess

# Structured facts about a move, for the commentary system (Phase 9). This module only reads
# the board: it has no engine, GUI or dialogue imports, and it never picks a move.
# events_for_move reports only facts python-chess can prove. The judgement kinds (INACCURACY,
# MISTAKE, BLUNDER, MISSED_WIN) are never made here: judgement.py makes them from numbers that
# a caller measured with an engine.

BY = ("player", "stockfih")


class EventKind(Enum):
    MOVE = "move"  # every legal move gets one
    CAPTURE = "capture"
    CASTLE = "castle"
    PROMOTION = "promotion"
    CHECK = "check"  # check that is not mate
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    DRAW = "draw"  # any other draw; `reason` says which
    # Judgements, made by judgement.py from engine scores (never by events_for_move):
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"
    MISSED_WIN = "missed_win"
    # Facts about the game as a whole, made by game_events.py from numbers and headers:
    MAJOR_SWING = "major_swing"  # the evaluation changed a lot, whoever moved
    GAME_WON = "game_won"  # from the player's side
    GAME_LOST = "game_lost"
    GAME_DRAWN = "game_drawn"
    OPENING = "opening"  # name taken from the PGN headers only


@dataclass(frozen=True)
class GameEvent:
    kind: EventKind
    by: str  # "player" or "stockfih": who played the move
    ply: int  # 1 = White's first move
    san: str  # the move in standard notation
    color: chess.Color  # side that moved
    captured: chess.PieceType | None = None  # CAPTURE only
    winner: chess.Color | None = None  # CHECKMATE only
    reason: str = ""  # DRAW only, e.g. "insufficient_material"
    loss: int | None = None  # judgements only: centipawns lost, None when a mate score was involved


def _outcome(board: chess.Board) -> chess.Outcome | None:
    # Same rule as Game.outcome: threefold and 50-move are applied once they have happened.
    out = board.outcome()
    if out is not None:
        return out
    if board.is_repetition(3):
        return chess.Outcome(chess.Termination.THREEFOLD_REPETITION, None)
    if board.is_fifty_moves():
        return chess.Outcome(chess.Termination.FIFTY_MOVES, None)
    return None


def check_move(board: chess.Board, move: chess.Move, by: str) -> None:
    # Raises ValueError for an unknown `by` or a move that is not legal in `board`.
    if by not in BY:
        raise ValueError(f"by must be one of {BY}.")
    if move not in board.legal_moves:
        raise ValueError(f"Illegal move {move.uci()} in {board.fen()}")


def events_for_move(board: chess.Board, move: chess.Move, by: str) -> list[GameEvent]:
    # `board` is the position BEFORE the move; it is left unchanged. Returns the events of
    # this move in a fixed order: MOVE, then CAPTURE, CASTLE, PROMOTION, CHECK, and last the
    # game-ending one (CHECKMATE, STALEMATE or DRAW) if the move ended the game.
    # Raises ValueError for an illegal move or an unknown `by`.
    check_move(board, move, by)
    color = board.turn
    ply = board.ply() + 1
    san = board.san(move)
    captured = None
    if board.is_capture(move):
        captured = chess.PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
    castle = board.is_castling(move)
    after = board.copy()
    after.push(move)
    out = _outcome(after)

    def event(kind: EventKind, **extra) -> GameEvent:
        return GameEvent(kind, by, ply, san, color, **extra)

    events = [event(EventKind.MOVE)]
    if captured is not None:
        events.append(event(EventKind.CAPTURE, captured=captured))
    if castle:
        events.append(event(EventKind.CASTLE))
    if move.promotion:
        events.append(event(EventKind.PROMOTION))
    if after.is_check() and not after.is_checkmate():
        events.append(event(EventKind.CHECK))
    if out is not None:
        if out.termination == chess.Termination.CHECKMATE:
            events.append(event(EventKind.CHECKMATE, winner=out.winner))
        elif out.termination == chess.Termination.STALEMATE:
            events.append(event(EventKind.STALEMATE))
        else:
            events.append(event(EventKind.DRAW, reason=out.termination.name.lower()))
    return events
