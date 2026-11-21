from enum import Enum

import chess

# The phase of a game, for the commentary only: it lets a comment avoid saying something that
# the position contradicts (an opening remark at move 40). It reads the board and nothing
# else: no engine, no GUI, no dialogue, and it never touches a move.
# The numbers are design numbers, tune later.
# shortcut: material and move number only. A middlegame position loaded from a FEN that
# says "move 1" counts as opening. Upgrade if that ever shows up in play.

OPENING_MAX_MOVE = 10  # full moves; after this a game with plenty of material is a middlegame
ENDGAME_MAX_MATERIAL = 24  # both sides together, in POINTS; the starting position has 62
POINTS = {chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


class Phase(Enum):
    OPENING = "opening"
    MIDDLEGAME = "middlegame"
    ENDGAME = "endgame"


def non_pawn_material(board: chess.Board) -> int:
    # Knights, bishops, rooks and queens of both sides, in points. Pawns and kings do not count.
    return sum(
        points * len(board.pieces(piece, color))
        for piece, points in POINTS.items()
        for color in (chess.WHITE, chess.BLACK)
    )


def game_phase(board: chess.Board) -> Phase:
    # Little material left is an endgame whatever the move number says.
    if non_pawn_material(board) <= ENDGAME_MAX_MATERIAL:
        return Phase.ENDGAME
    if board.fullmove_number <= OPENING_MAX_MOVE:
        return Phase.OPENING
    return Phase.MIDDLEGAME
