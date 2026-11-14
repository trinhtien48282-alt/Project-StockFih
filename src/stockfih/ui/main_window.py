from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton, QVBoxLayout, QWidget

from stockfih.chess.game import Game
from stockfih.ui.chessboard import BoardWidget
from stockfih.ui.sidebar import Sidebar
from stockfih.ui.themes import PIECE_THEMES, SQUARE_THEMES


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("StockFih")
        self.settings = QSettings("StockFih", "StockFih")
        self.choice = {
            "square": self._saved("square", SQUARE_THEMES),
            "piece": self._saved("piece", PIECE_THEMES),
        }
        self.game = Game()
        self.board = BoardWidget(self.game)
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(240)
        self.board.changed.connect(self._refresh)
        self._apply_themes()

        view = self.menuBar().addMenu("View")
        self._theme_menu(view, "Square theme", "square", SQUARE_THEMES)
        self._theme_menu(view, "Piece theme", "piece", PIECE_THEMES)

        side = QVBoxLayout()
        side.addWidget(self.sidebar, 1)
        controls = (
            ("New game", "Ctrl+N", self._act(self.game.new_game)),
            ("Restart", "Ctrl+R", self._act(self.game.restart)),
            ("Undo", "Ctrl+Z", self._act(self.game.undo)),
            ("Redo", "Ctrl+Y", self._act(self.game.redo)),
            ("Flip board", "F", self.board.flip),
        )
        for label, key, slot in controls:
            button = QPushButton(f"{label} ({key})")
            button.clicked.connect(slot)
            side.addWidget(button)
            QShortcut(QKeySequence(key), self, activated=slot)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.addWidget(self.board, 1)
        layout.addLayout(side)
        self.setCentralWidget(root)
        self.resize(1000, 760)
        self._refresh()

    def _saved(self, key: str, themes: dict) -> str:
        # Stored value is external data: fall back to the default if it is unknown.
        value = str(self.settings.value(key, ""))
        return value if value in themes else next(iter(themes))

    def _theme_menu(self, view, label: str, key: str, themes: dict) -> None:
        menu = view.addMenu(label)
        group = QActionGroup(self)
        for name in themes:
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(name == self.choice[key])
            action.triggered.connect(lambda _=False, n=name: self._choose(key, n))
            group.addAction(action)
            menu.addAction(action)

    def _choose(self, key: str, name: str) -> None:
        self.choice[key] = name
        self.settings.setValue(key, name)
        self._apply_themes()

    def _apply_themes(self) -> None:
        self.board.set_themes(
            SQUARE_THEMES[self.choice["square"]], PIECE_THEMES[self.choice["piece"]]
        )

    def _act(self, change):
        def run() -> None:
            change()
            self.board.refresh()

        return run

    def _refresh(self) -> None:
        self.sidebar.set_info(self.game.status(), self.game.history_text())
