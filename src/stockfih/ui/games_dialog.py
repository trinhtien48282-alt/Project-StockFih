from PySide6.QtCore import QRunnable, QThreadPool
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stockfih.services import chesscom
from stockfih.services.chesscom import ArchiveGame, ChessComError
from stockfih.ui.chesscom_dialog import _date, _Signals

# shortcut: keeps the last few months in memory so revisiting one is instant. A busy month
# can be many MB, hence the small cap. Upgrade to a disk cache if people ask for it.
CACHE_MONTHS = 6


class _Job(QRunnable):
    # Runs one request on a pool thread so the window never freezes. Requests are made one
    # at a time (the dialog disables its buttons meanwhile), which is what the PubAPI asks for.
    def __init__(self, work, signals: _Signals) -> None:
        super().__init__()
        self.work = work
        self.signals = signals

    def run(self) -> None:
        try:
            self._send(self.signals.done, self.work())
        except ChessComError as error:
            self._send(self.signals.failed, str(error))
        except Exception as error:  # a worker thread must never die silently
            self._send(self.signals.failed, f"Unexpected error: {error}")

    def _send(self, signal, value) -> None:
        try:
            signal.emit(value)
        except RuntimeError:  # dialog was closed while the request was running
            pass


def describe(game: ArchiveGame) -> str:
    def side(name: str, rating: int | None) -> str:
        return name if rating is None else f"{name} ({rating})"

    parts = [
        _date(game.end_time) or "?",
        f"{side(game.white, game.white_rating)} vs {side(game.black, game.black_rating)}",
        game.result or "?",
    ]
    if game.time_class:
        parts.append(game.time_class)
    return "   ".join(parts)


class GamesDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.pgn: str | None = None  # set when the user opens a game
        self._games: list[ArchiveGame] = []
        self._name = ""
        self._key: tuple[str, int, int] | None = None  # month being loaded
        self._cache: dict[tuple[str, int, int], list[ArchiveGame]] = {}
        self._working = False
        self.setWindowTitle("Chess.com public games")
        self.resize(600, 480)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Chess.com username")
        self.name.setMaxLength(25)
        self.find = QPushButton("Find games")
        self.find.setDefault(True)  # Enter in the name box clicks it
        self.months = QComboBox()
        self.games = QListWidget()
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.open = QPushButton("Open game")
        self.open.setAutoDefault(False)
        close = QPushButton("Close")
        close.setAutoDefault(False)
        row = QHBoxLayout()
        row.addWidget(self.name, 1)
        row.addWidget(self.find)
        bottom = QHBoxLayout()
        bottom.addWidget(self.status, 1)
        bottom.addWidget(self.open)
        bottom.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.months)
        layout.addWidget(self.games, 1)
        layout.addLayout(bottom)
        note = QLabel("Public Chess.com data, read-only. Standard chess only. It can lag behind the website.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.find.clicked.connect(self._find)
        self.months.activated.connect(self._load_month)  # user picks only, not programmatic fills
        self.games.currentRowChanged.connect(lambda _row: self._sync())
        self.games.itemDoubleClicked.connect(lambda _item: self._open())
        self.open.clicked.connect(self._open)
        close.clicked.connect(self.reject)
        self._sync()

    def _sync(self) -> None:
        self.find.setEnabled(not self._working)
        self.months.setEnabled(not self._working and self.months.count() > 0)
        self.open.setEnabled(not self._working and self.games.currentRow() >= 0)

    def _run(self, work, done, message: str) -> None:
        self.status.setText(message)
        self._working = True
        self._sync()
        signals = _Signals(self)
        signals.done.connect(done)  # must be a bound method of this dialog, not a lambda:
        signals.failed.connect(self._fail)  # that keeps the slot on the GUI thread
        QThreadPool.globalInstance().start(_Job(work, signals))

    def _fail(self, message: str) -> None:
        self.status.setText(message)
        self._working = False
        self._sync()

    def _find(self, _checked: bool = False) -> None:
        if self._working:
            return
        try:
            name = chesscom.clean_username(self.name.text())
        except ChessComError as error:
            self.status.setText(str(error))
            return
        self._name = name
        self.months.clear()
        self.games.clear()
        self._games = []
        self._run(lambda: chesscom.fetch_archives(name), self._got_months, "Looking up...")

    def _got_months(self, months: list) -> None:
        for year, month in months:
            self.months.addItem(f"{year}-{month:02d}", (year, month))
        if not months:
            self.status.setText("No public games found for this player.")
            self._working = False
            self._sync()
            return
        self._load_month()

    def _load_month(self, _index: int = 0) -> None:
        if self._working:
            return
        year, month = self.months.currentData()
        name = self._name
        self.games.clear()
        self._games = []
        self._key = (name, year, month)
        if self._key in self._cache:
            self._got_games(self._cache[self._key])
            return
        self._run(
            lambda: chesscom.fetch_month(name, year, month),
            self._got_games,
            f"Loading {year}-{month:02d}... (big months can take a while)",
        )

    def _got_games(self, games: list) -> None:
        self._games = games
        if self._key is not None:
            if self._key not in self._cache and len(self._cache) >= CACHE_MONTHS:
                del self._cache[next(iter(self._cache))]  # oldest first
            self._cache[self._key] = games
        self.games.addItems([describe(game) for game in games])  # plain text: names are external data
        self.status.setText(f"{len(games)} game(s)." if games else "No standard chess games this month.")
        self._working = False
        self._sync()

    def _open(self, _checked: bool = False) -> None:
        row = self.games.currentRow()
        if not self._working and 0 <= row < len(self._games):
            self.pgn = self._games[row].pgn
            self.accept()


def ask_chesscom_pgn(parent: QWidget) -> str | None:
    # PGN of the game the user opened, or None.
    dialog = GamesDialog(parent)
    return dialog.pgn if dialog.exec() == QDialog.DialogCode.Accepted else None
