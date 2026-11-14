import chess
from PySide6.QtWidgets import QInputDialog, QWidget

_PIECES = {
    "Queen": chess.QUEEN,
    "Rook": chess.ROOK,
    "Bishop": chess.BISHOP,
    "Knight": chess.KNIGHT,
}


def ask_promotion(parent: QWidget) -> chess.PieceType | None:
    name, ok = QInputDialog.getItem(parent, "Promotion", "Promote pawn to:", list(_PIECES), 0, False)
    return _PIECES[name] if ok else None
