from PySide6.QtCore import QByteArray, QSettings
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stockfih.chess.game import Game
from stockfih.ui.chessboard import BoardWidget
from stockfih.ui.dialogs import ask_fen, ask_game_info, ask_open_pgn, ask_save_pgn
from stockfih.ui.sidebar import Sidebar
from stockfih.ui.sounds import Sounds
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
        self.sounds = Sounds(self)
        self.board.animate = self.settings.value("animate", True, type=bool)
        self.sounds.enabled = self.settings.value("sound", True, type=bool)
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(240)
        self.board.changed.connect(self._refresh)
        self.board.moved.connect(self._play_move_sound)
        self._apply_themes()

        file_menu = self.menuBar().addMenu("File")
        for label, key, slot in (
            ("Open PGN...", "Ctrl+O", self._open_pgn),
            ("Save PGN...", "Ctrl+S", self._save_pgn),
            ("Load FEN...", "Ctrl+L", self._load_fen),
            ("Copy FEN", "Ctrl+Shift+C", self._copy_fen),
            ("Game info...", "Ctrl+I", self._game_info),
        ):
            action = file_menu.addAction(label)
            action.setShortcut(QKeySequence(key))
            action.triggered.connect(slot)

        view = self.menuBar().addMenu("View")
        self._theme_menu(view, "Square theme", "square", SQUARE_THEMES)
        self._theme_menu(view, "Piece theme", "piece", PIECE_THEMES)
        view.addSeparator()
        self._option(view, "Animate moves", "animate", self.board, "animate")
        self._option(view, "Sound", "sound", self.sounds, "enabled")

        side = QVBoxLayout()
        side.addWidget(self.sidebar, 1)
        controls = (
            ("New game", ("Ctrl+N",), self._act(self.game.new_game)),
            ("Restart", ("Ctrl+R",), self._act(self.game.restart)),
            ("Undo", ("Ctrl+Z", "Left"), self._act(self.game.undo)),
            ("Redo", ("Ctrl+Y", "Right"), self._act(self.game.redo, forward=True)),
            ("Flip board", ("F",), self.board.flip),
        )
        for label, keys, slot in controls:
            button = QPushButton(f"{label} ({keys[0]})")
            button.clicked.connect(slot)
            side.addWidget(button)
            for key in keys:
                QShortcut(QKeySequence(key), self, activated=slot)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.addWidget(self.board, 1)
        layout.addLayout(side)
        self.setCentralWidget(root)
        saved = self.settings.value("geometry")
        if not (
            isinstance(saved, (QByteArray, bytes)) and self.restoreGeometry(QByteArray(saved))
        ):
            self.resize(1000, 760)
        self._refresh()

    def closeEvent(self, event) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

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

    def _option(self, view, label: str, key: str, target, attr: str) -> None:
        # A checkable on/off setting: flips target.attr and remembers it between runs.
        action = QAction(label, self)
        action.setCheckable(True)
        action.setChecked(getattr(target, attr))

        def toggled(on: bool) -> None:
            setattr(target, attr, on)
            self.settings.setValue(key, on)

        action.toggled.connect(toggled)
        view.addAction(action)

    def _choose(self, key: str, name: str) -> None:
        self.choice[key] = name
        self.settings.setValue(key, name)
        self._apply_themes()

    def _apply_themes(self) -> None:
        self.board.set_themes(
            SQUARE_THEMES[self.choice["square"]], PIECE_THEMES[self.choice["piece"]]
        )

    def _act(self, change, forward: bool = False):
        # forward=True: stepping ahead in the game (redo), so slide the piece and play a sound.
        def run() -> None:
            done = change()
            self.board.refresh(animate=forward and bool(done))
            if forward and done:
                self._play_move_sound()

        return run

    def _play_move_sound(self) -> None:
        if self.game.outcome() is not None:
            self.sounds.play("end")
        elif self.game.last_capture:
            self.sounds.play("capture")
        else:
            self.sounds.play("move")

    def _open_pgn(self) -> None:
        path = ask_open_pgn(self)
        if path is None:
            return
        try:
            self.game.load_pgn(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Open PGN", str(error))
            return
        self.board.refresh()

    def _save_pgn(self) -> None:
        path = ask_save_pgn(self)
        if path is None:
            return
        try:
            path.write_text(self.game.export_pgn(), encoding="utf-8")
        except OSError as error:
            QMessageBox.warning(self, "Save PGN", str(error))

    def _load_fen(self) -> None:
        fen = ask_fen(self)
        if fen is None:
            return
        try:
            self.game.load_fen(fen)
        except ValueError as error:
            QMessageBox.warning(self, "Load FEN", str(error))
            return
        self.board.refresh()

    def _copy_fen(self) -> None:
        QApplication.clipboard().setText(self.game.board.fen())
        self.statusBar().showMessage("FEN copied to clipboard", 3000)

    def _game_info(self) -> None:
        values = ask_game_info(self, self.game.info(), self.game.extra_info())
        if values is None:
            return
        try:
            self.game.set_info(values)
        except ValueError as error:
            QMessageBox.warning(self, "Game info", str(error))
            return
        self._refresh()

    def _refresh(self) -> None:
        self.setWindowTitle(self.game.title())
        self.sidebar.set_info(self.game.status(), self.game.history_text())
