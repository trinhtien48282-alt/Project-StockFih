import chess

CENTER = (chess.D4, chess.D5, chess.E4, chess.E5)
ATTACK_CP = 5  # centipawns per attacker on a central square. Tune in Phase 14.


def _attacks(board: chess.Board, color: chess.Color) -> int:
    return sum(len(board.attackers(color, square)) for square in CENTER)


def center_control(board: chess.Board) -> int:
    # White minus Black, in centipawns, from how many pieces and pawns hit d4, d5, e4, e5.
    # shortcut: attacks only. Occupying the center is not rewarded yet.
    return ATTACK_CP * (_attacks(board, chess.WHITE) - _attacks(board, chess.BLACK))
