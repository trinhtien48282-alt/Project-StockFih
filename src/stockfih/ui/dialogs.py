from pathlib import Path

import chess
from PySide6.QtWidgets import QFileDialog, QInputDialog, QWidget

_PIECES = {
    "Queen": chess.QUEEN,
    "Rook": chess.ROOK,
    "Bishop": chess.BISHOP,
    "Knight": chess.KNIGHT,
}

_PGN_FILTER = "PGN files (*.pgn);;All files (*)"


def ask_promotion(parent: QWidget) -> chess.PieceType | None:
    name, ok = QInputDialog.getItem(parent, "Promotion", "Promote pawn to:", list(_PIECES), 0, False)
    return _PIECES[name] if ok else None


def ask_fen(parent: QWidget) -> str | None:
    text, ok = QInputDialog.getText(parent, "Load FEN", "FEN:")
    text = text.strip()
    return text if ok and text else None


def ask_open_pgn(parent: QWidget) -> Path | None:
    name, _ = QFileDialog.getOpenFileName(parent, "Open PGN", "", _PGN_FILTER)
    return Path(name) if name else None


def ask_save_pgn(parent: QWidget) -> Path | None:
    name, _ = QFileDialog.getSaveFileName(parent, "Save PGN", "game.pgn", _PGN_FILTER)
    if not name:
        return None
    path = Path(name)
    return path if path.suffix else path.with_suffix(".pgn")
