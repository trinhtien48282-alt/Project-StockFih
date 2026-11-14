from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

AVATAR_PX = 48


class Sidebar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.avatar = QLabel()
        self.avatar.setFixedSize(AVATAR_PX, AVATAR_PX)
        self.name = QLabel()
        self.name.setTextFormat(Qt.TextFormat.PlainText)
        self.name.setWordWrap(True)
        self.name.setStyleSheet("font-weight: bold; font-size: 15px;")
        head = QHBoxLayout()
        head.addWidget(self.avatar)
        head.addWidget(self.name, 1)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet("font-weight: bold; font-size: 15px;")
        self.history = QPlainTextEdit()
        self.history.setReadOnly(True)
        self.history.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(head)
        layout.addWidget(self.status)
        layout.addWidget(self.history, 1)

    def set_profile(self, username: str, avatar: QPixmap | None) -> None:
        self.name.setText(username)
        if avatar is None:
            self.avatar.clear()
        else:
            self.avatar.setPixmap(
                avatar.scaled(
                    AVATAR_PX,
                    AVATAR_PX,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def set_info(self, status: str, history: str) -> None:
        self.status.setText(status)
        self.history.setPlainText(history)
