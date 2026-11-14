from pathlib import Path

import chess
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QWidget,
)

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


def ask_game_info(
    parent: QWidget, fields: dict[str, str], readonly: dict[str, str]
) -> dict[str, str] | None:
    dialog = QDialog(parent)
    dialog.setWindowTitle("Game info")
    dialog.setMinimumWidth(360)
    form = QFormLayout(dialog)
    edits = {}
    for key, value in fields.items():
        edits[key] = QLineEdit(value)
        form.addRow(key, edits[key])
    for key, value in readonly.items():
        label = QLabel(value)
        label.setTextFormat(Qt.TextFormat.PlainText)  # PGN text is external data
        form.addRow(key, label)
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return {key: edit.text() for key, edit in edits.items()}


def ask_open_pgn(parent: QWidget) -> Path | None:
    name, _ = QFileDialog.getOpenFileName(parent, "Open PGN", "", _PGN_FILTER)
    return Path(name) if name else None


def ask_save_pgn(parent: QWidget) -> Path | None:
    name, _ = QFileDialog.getSaveFileName(parent, "Save PGN", "game.pgn", _PGN_FILTER)
    if not name:
        return None
    path = Path(name)
    return path if path.suffix else path.with_suffix(".pgn")
