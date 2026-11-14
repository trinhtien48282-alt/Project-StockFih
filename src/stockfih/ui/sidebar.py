from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget


class Sidebar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet("font-weight: bold; font-size: 15px;")
        self.history = QPlainTextEdit()
        self.history.setReadOnly(True)
        self.history.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.status)
        layout.addWidget(self.history, 1)

    def set_info(self, status: str, history: str) -> None:
        self.status.setText(status)
        self.history.setPlainText(history)
