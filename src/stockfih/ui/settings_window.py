from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSlider,
    QWidget,
)

from stockfih.ui.app_theme import THEMES
from stockfih.ui.themes import PIECE_THEMES, SQUARE_THEMES


def _combo(names, current: str) -> QComboBox:
    box = QComboBox()
    box.addItems(list(names))
    box.setCurrentIndex(box.findText(current))  # setCurrentText does nothing on a plain combo
    return box


def ask_settings(parent: QWidget, values: dict) -> dict | None:
    # values/result keys: theme, square, piece (names), animate, sound (bool), volume (0-100).
    # Returns the new values, or None if cancelled.
    dialog = QDialog(parent)
    dialog.setWindowTitle("Settings")
    dialog.setMinimumWidth(360)
    form = QFormLayout(dialog)
    theme = _combo(THEMES, values["theme"])
    square = _combo(SQUARE_THEMES, values["square"])
    piece = _combo(PIECE_THEMES, values["piece"])
    animate = QCheckBox("Animate moves")
    animate.setChecked(values["animate"])
    sound = QCheckBox("Sound effects")
    sound.setChecked(values["sound"])
    volume = QSlider(Qt.Orientation.Horizontal)
    volume.setRange(0, 100)
    volume.setValue(values["volume"])
    form.addRow("App theme", theme)
    form.addRow("Square theme (this profile)", square)
    form.addRow("Piece theme (this profile)", piece)
    form.addRow(animate)
    form.addRow(sound)
    form.addRow("Volume", volume)
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return {
        "theme": theme.currentText(),
        "square": square.currentText(),
        "piece": piece.currentText(),
        "animate": animate.isChecked(),
        "sound": sound.isChecked(),
        "volume": volume.value(),
    }
