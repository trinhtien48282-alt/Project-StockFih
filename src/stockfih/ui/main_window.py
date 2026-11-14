from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget

from stockfih.chess.game import Game
from stockfih.ui.chessboard import BoardWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("StockFih")
        self.board = BoardWidget(Game())
        flip = QPushButton("Flip board (F)")
        flip.clicked.connect(self.board.flip)
        QShortcut(QKeySequence("F"), self, activated=self.board.flip)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addWidget(self.board, 1)
        layout.addWidget(flip)
        self.setCentralWidget(root)
        self.resize(700, 760)