from PySide6.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QLabel, QVBoxLayout, QWidget

# shortcut: a hand-kept list, so it must match the keys set in main_window.py. Update both.
SHORTCUTS = (
    ("Ctrl+N", "New game"),
    ("Ctrl+R", "Restart"),
    ("Ctrl+Z / Left", "Undo"),
    ("Ctrl+Y / Right", "Redo"),
    ("F", "Flip board"),
    ("Ctrl+O", "Open PGN"),
    ("Ctrl+S", "Save PGN"),
    ("Ctrl+L", "Load FEN"),
    ("Ctrl+Shift+C", "Copy FEN"),
    ("Ctrl+I", "Game info"),
    ("Ctrl+,", "Settings"),
    ("F1", "This list"),
)


def show_shortcuts(parent: QWidget) -> None:
    dialog = QDialog(parent)
    dialog.setWindowTitle("Keyboard shortcuts")
    grid = QGridLayout()
    for row, (keys, action) in enumerate(SHORTCUTS):
        grid.addWidget(QLabel(keys), row, 0)
        grid.addWidget(QLabel(action), row, 1)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(dialog.reject)
    layout = QVBoxLayout(dialog)
    layout.addLayout(grid)
    layout.addWidget(buttons)
    dialog.exec()
