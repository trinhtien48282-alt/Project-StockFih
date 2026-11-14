from pathlib import Path

import chess
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stockfih.profiles.player import GameRecord
from stockfih.profiles.statistics import Stats, outcome_for

_PIECES = {
    "Queen": chess.QUEEN,
    "Rook": chess.ROOK,
    "Bishop": chess.BISHOP,
    "Knight": chess.KNIGHT,
}

_PGN_FILTER = "PGN files (*.pgn);;All files (*)"
_IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*)"


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


def ask_profile(
    parent: QWidget, title: str, username: str = ""
) -> tuple[str, Path | None] | None:
    # Returns (username, new avatar image or None to leave the avatar alone).
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(340)
    form = QFormLayout(dialog)
    name = QLineEdit(username)
    name.setMaxLength(24)
    form.addRow("Username", name)
    chosen: list[Path] = []
    label = QLabel()
    label.setTextFormat(Qt.TextFormat.PlainText)  # file name is external data
    button = QPushButton("Choose avatar...")

    def pick(_checked: bool = False) -> None:
        path, _ = QFileDialog.getOpenFileName(dialog, "Choose avatar", "", _IMAGE_FILTER)
        if path:
            chosen[:] = [Path(path)]
            label.setText(Path(path).name)

    button.clicked.connect(pick)
    row = QHBoxLayout()
    row.addWidget(button)
    row.addWidget(label, 1)
    form.addRow("Avatar", row)
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return name.text(), (chosen[0] if chosen else None)


def ask_history(parent: QWidget, games: list[GameRecord]) -> str | None:
    # Returns the PGN of the chosen game, or None.
    dialog = QDialog(parent)
    dialog.setWindowTitle("Game history")
    dialog.resize(480, 360)
    layout = QVBoxLayout(dialog)
    if not games:
        layout.addWidget(QLabel("No finished games yet."))
    games_list = QListWidget()
    for game in games:
        item = QListWidgetItem(f"{game.played}   {game.result}   {game.white} vs {game.black}")
        item.setData(Qt.ItemDataRole.UserRole, game.pgn)
        games_list.addItem(item)
    layout.addWidget(games_list, 1)
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Close
    )

    def choose() -> None:
        if games_list.currentItem() is not None:
            dialog.accept()

    buttons.accepted.connect(choose)
    buttons.rejected.connect(dialog.reject)
    games_list.itemDoubleClicked.connect(lambda _item: choose())
    layout.addWidget(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    item = games_list.currentItem()
    return item.data(Qt.ItemDataRole.UserRole) if item else None


def show_stats(parent: QWidget, stats: Stats, recent: list[GameRecord]) -> None:
    dialog = QDialog(parent)
    dialog.setWindowTitle("Statistics")
    dialog.setMinimumWidth(420)
    layout = QVBoxLayout(dialog)
    lines = [
        f"Games: {stats.total}",
        f"Wins: {stats.wins}    Losses: {stats.losses}    Draws: {stats.draws}",
        "Win rate: " + ("n/a" if stats.win_rate is None else f"{stats.win_rate:.1%}"),
    ]
    if stats.unscored:
        lines.append(f"{stats.unscored} game(s) have no recorded color and are not scored.")
    lines += ["", "Recent games" if recent else "No finished games yet."]
    for game in recent:
        outcome = outcome_for(game.result, game.color) or "not scored"
        lines.append(f"{game.played}   {outcome}   {game.white} vs {game.black}")
    label = QLabel("\n".join(lines))
    label.setTextFormat(Qt.TextFormat.PlainText)  # names come from PGN text
    layout.addWidget(label)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.exec()
