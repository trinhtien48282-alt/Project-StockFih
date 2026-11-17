import logging
from PySide6.QtCore import QRunnable, QThreadPool
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from stockfih.services import chesscom
from stockfih.services.chesscom import BOARDS, ChessComError, LeaderEntry
from stockfih.ui.chesscom_dialog import _Signals

_COLUMNS = ("Rank", "Player", "Score", "W", "L", "D", "Country")


class _Load(QRunnable):
    # Pool thread, so the window never freezes. One request fetches all three boards.
    def __init__(self, signals: _Signals) -> None:
        super().__init__()
        self.signals = signals

    def run(self) -> None:
        try:
            self._send(self.signals.done, chesscom.fetch_leaderboards())
        except ChessComError as error:
            self._send(self.signals.failed, str(error))
        except Exception as error:  # a worker thread must never die silently
            self._send(self.signals.failed, f"Unexpected error: {error}")

        except Exception as error:  # a worker thread must never die silently
            logging.getLogger(__name__).exception("Chess.com request failed")
            self._send(self.signals.failed, f"Unexpected error: {error}")

    def _send(self, signal, value) -> None:
        try:
            signal.emit(value)
        except RuntimeError:  # dialog was closed while the request was running
            pass


def _n(value: int | None) -> str:
    return "-" if value is None else str(value)


def row_values(entry: LeaderEntry) -> tuple[str, ...]:
    player = f"{entry.title} {entry.username}" if entry.title else entry.username
    return (
        str(entry.rank),
        player,
        str(entry.score),
        _n(entry.wins),
        _n(entry.losses),
        _n(entry.draws),
        entry.country or "-",
    )


def _table(entries: list[LeaderEntry]) -> QTableWidget:
    table = QTableWidget(len(entries), len(_COLUMNS))
    table.setHorizontalHeaderLabels(_COLUMNS)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    for row, entry in enumerate(entries):
        for col, text in enumerate(row_values(entry)):
            table.setItem(row, col, QTableWidgetItem(text))  # plain text: names are external data
    table.resizeColumnsToContents()
    table.horizontalHeader().setStretchLastSection(True)
    return table


class LeaderboardDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Chess.com leaderboards")
        self.resize(560, 520)
        self.status = QLabel("Loading...")
        self.status.setWordWrap(True)
        self.tabs = QTabWidget()
        note = QLabel("Chess.com ratings, top 50 per board. Public read-only data; it can lag behind the website.")
        note.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(note)
        signals = _Signals(self)
        signals.done.connect(self._show)
        signals.failed.connect(self._fail)
        QThreadPool.globalInstance().start(_Load(signals))

    def _show(self, boards: dict) -> None:
        self.status.setText("")
        for key, label in BOARDS:
            entries = boards.get(key, [])
            if entries:
                self.tabs.addTab(_table(entries), label)
            else:
                self.tabs.addTab(QLabel(f"Chess.com sent no {label} leaderboard."), label)

    def _fail(self, message: str) -> None:
        self.status.setText(message)
