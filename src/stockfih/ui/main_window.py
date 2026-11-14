from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings, QStandardPaths
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
from stockfih.profiles.player import Profile, ProfileStore
from stockfih.profiles.statistics import compute
from stockfih.ui.avatar import load_avatar, save_avatar
from stockfih.ui.chessboard import BoardWidget
from stockfih.ui.dialogs import (
    ask_fen,
    ask_game_info,
    ask_history,
    ask_open_pgn,
    ask_profile,
    ask_save_pgn,
    show_stats,
)
from stockfih.ui.sidebar import Sidebar
from stockfih.ui.sounds import Sounds
from stockfih.ui.themes import PIECE_THEMES, SQUARE_THEMES


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("StockFih")
        self.settings = QSettings("StockFih", "StockFih")
        self.data_dir = Path(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        )
        self.store = ProfileStore(self.data_dir / "stockfih.db")
        self.profile = self._start_profile()
        self.choice = {
            "square": next(iter(SQUARE_THEMES)),
            "piece": next(iter(PIECE_THEMES)),
        }
        self._theme_actions: dict[str, dict[str, QAction]] = {}
        self._options: dict[str, tuple[QAction, object, str]] = {}
        self._color_actions: dict[str, QAction] = {}
        self._last_saved: str | None = None  # PGN of the last game written to history
        self.game = Game()
        self.board = BoardWidget(self.game)
        self.sounds = Sounds(self)
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(240)
        self.board.changed.connect(self._refresh)
        self.board.moved.connect(self._play_move_sound)
        self.board.moved.connect(self._record_game)

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

        profile_menu = self.menuBar().addMenu("Profile")
        profile_menu.addAction("New profile...").triggered.connect(self._new_profile)
        profile_menu.addAction("Edit profile...").triggered.connect(self._edit_profile)
        self._switch_menu = profile_menu.addMenu("Switch profile")
        color_menu = profile_menu.addMenu("Play as")
        color_group = QActionGroup(self)
        for color in ("white", "black"):
            action = QAction(color.capitalize(), self)
            action.setCheckable(True)
            action.triggered.connect(lambda _=False, c=color: self._set_color(c))
            color_group.addAction(action)
            color_menu.addAction(action)
            self._color_actions[color] = action
        profile_menu.addAction("Game history...").triggered.connect(self._show_history)
        profile_menu.addAction("Statistics...").triggered.connect(self._show_stats)
        profile_menu.aboutToShow.connect(self._fill_switch_menu)
        self._fill_switch_menu()

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
        self._apply_prefs()
        self._show_profile()
        self._refresh()

    def closeEvent(self, event) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        self.store.close()
        super().closeEvent(event)

    # --- profiles ---

    def _start_profile(self) -> Profile:
        profiles = self.store.profiles()
        if not profiles:
            return self.store.create("Player")  # rename it via Profile > Edit profile
        saved = self.settings.value("profile", 0, type=int)
        return next((p for p in profiles if p.id == saved), profiles[0])

    def _avatar_file(self, profile: Profile) -> Path:
        return self.data_dir / "avatars" / f"{profile.id}.png"

    def _show_profile(self) -> None:
        self.sidebar.set_profile(self.profile.username, load_avatar(self._avatar_file(self.profile)))

    def _set_avatar(self, profile: Profile, image: Path | None) -> None:
        if image is None:
            return
        try:
            save_avatar(image, self._avatar_file(profile))
        except ValueError as error:
            QMessageBox.warning(self, "Avatar", str(error))

    def _switch(self, profile: Profile) -> None:
        self.profile = profile
        self.settings.setValue("profile", profile.id)
        self._apply_prefs()
        self._show_profile()

    def _fill_switch_menu(self) -> None:
        self._switch_menu.clear()
        group = QActionGroup(self._switch_menu)
        for profile in self.store.profiles():
            # "&" would turn the next letter into a menu shortcut, so double it.
            action = self._switch_menu.addAction(profile.username.replace("&", "&&"))
            action.setCheckable(True)
            action.setChecked(profile.id == self.profile.id)
            group.addAction(action)
            action.triggered.connect(lambda _=False, p=profile: self._switch(p))

    def _new_profile(self) -> None:
        result = ask_profile(self, "New profile")
        if result is None:
            return
        name, image = result
        try:
            profile = self.store.create(name)
        except ValueError as error:
            QMessageBox.warning(self, "New profile", str(error))
            return
        self._set_avatar(profile, image)
        self._switch(profile)

    def _edit_profile(self) -> None:
        result = ask_profile(self, "Edit profile", self.profile.username)
        if result is None:
            return
        name, image = result
        try:
            self.profile = self.store.rename(self.profile.id, name)
        except ValueError as error:
            QMessageBox.warning(self, "Edit profile", str(error))
            return
        self._set_avatar(self.profile, image)
        self._show_profile()

    def _show_history(self) -> None:
        pgn = ask_history(self, self.store.games(self.profile.id))
        if pgn is None:
            return
        try:
            self.game.load_pgn(pgn)
        except ValueError as error:
            QMessageBox.warning(self, "Game history", str(error))
            return
        self.board.refresh()

    def _record_game(self) -> None:
        # Runs after the player's move on the board. Only games finished by a move are recorded:
        # stepping to the end of an imported game with Redo is not a played game.
        if self.game.outcome() is None:
            return
        pgn = self.game.export_pgn()
        if pgn == self._last_saved:  # same finish reached again after Undo
            return
        self._last_saved = pgn
        info = self.game.info()
        self.store.add_game(
            self.profile.id, pgn, self.game.result(), info["White"], info["Black"], self._color()
        )

    # --- per-profile preferences ---

    def _theme_menu(self, view, label: str, key: str, themes: dict) -> None:
        menu = view.addMenu(label)
        group = QActionGroup(self)
        self._theme_actions[key] = {}
        for name in themes:
            action = QAction(name, self)
            action.setCheckable(True)
            action.triggered.connect(lambda _=False, n=name: self._choose(key, n))
            group.addAction(action)
            menu.addAction(action)
            self._theme_actions[key][name] = action

    def _option(self, view, label: str, key: str, target, attr: str) -> None:
        # A checkable on/off setting: flips target.attr and remembers it in the profile.
        action = QAction(label, self)
        action.setCheckable(True)

        def toggled(on: bool) -> None:
            setattr(target, attr, on)
            self.store.set_pref(self.profile.id, key, "1" if on else "0")

        action.toggled.connect(toggled)
        view.addAction(action)
        self._options[key] = (action, target, attr)

    def _apply_prefs(self) -> None:
        # Load the active profile's settings. Stored values are external data: unknown -> default.
        for key, themes in (("square", SQUARE_THEMES), ("piece", PIECE_THEMES)):
            name = self.store.pref(self.profile.id, key)
            self.choice[key] = name if name in themes else next(iter(themes))
            self._theme_actions[key][self.choice[key]].setChecked(True)
        for key, (action, target, attr) in self._options.items():
            on = self.store.pref(self.profile.id, key, "1") == "1"
            setattr(target, attr, on)
            action.blockSignals(True)  # do not write the value straight back
            action.setChecked(on)
            action.blockSignals(False)
        self._color_actions[self._color()].setChecked(True)
        self._apply_themes()

    def _color(self) -> str:
        color = self.store.pref(self.profile.id, "color", "white")
        return color if color in self._color_actions else "white"

    def _set_color(self, color: str) -> None:
        self.store.set_pref(self.profile.id, "color", color)

    def _show_stats(self) -> None:
        games = self.store.games(self.profile.id)
        show_stats(self, compute(games), games[:10])

    def _choose(self, key: str, name: str) -> None:
        self.choice[key] = name
        self.store.set_pref(self.profile.id, key, name)
        self._apply_themes()

    def _apply_themes(self) -> None:
        self.board.set_themes(
            SQUARE_THEMES[self.choice["square"]], PIECE_THEMES[self.choice["piece"]]
        )

    # --- game ---

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
        if not self.game.board.move_stack:
            self._last_saved = None  # fresh game: its finish is a new record
        self.setWindowTitle(self.game.title())
        self.sidebar.set_info(self.game.status(), self.game.history_text())
