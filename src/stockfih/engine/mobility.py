import chess

MOVE_CP = 2  # centipawns per extra legal-looking move. Small on purpose: tune in Phase 14.


def _count(board: chess.Board, color: chess.Color) -> int:
    # shortcut: pseudo-legal moves (no check or pin filtering), so a pinned piece still counts.
    # Cheap enough to run on every leaf; upgrade to legal moves if it skews play.
    probe = board.copy(stack=False)  # never touch the caller's board
    probe.turn = color
    return probe.pseudo_legal_moves.count()


def mobility(board: chess.Board) -> int:
    # White minus Black, in centipawns, from how many moves each side could play.
    return MOVE_CP * (_count(board, chess.WHITE) - _count(board, chess.BLACK))
