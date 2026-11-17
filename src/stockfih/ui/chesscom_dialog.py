import logging
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stockfih.services import chesscom
from stockfih.services.chesscom import ChessComError, ChessComProfile, RatingLine


class _Signals(QObject):
    done = Signal(object)  # (profile, ratings or None, note)
    failed = Signal(str)


class _Lookup(QRunnable):
    # Runs on a pool thread so the window never freezes. Requests go one after another,
    # which is what the PubAPI rate limit asks for.
    def __init__(self, username: str, signals: _Signals) -> None:
        super().__init__()
        self.username = username
        self.signals = signals

    def run(self) -> None:
        try:
            try:
                profile = chesscom.fetch_profile(self.username)
            except ChessComError as error:
                self._send(self.signals.failed, str(error))
                return
            try:
                ratings, note = chesscom.fetch_ratings(self.username), ""
            except ChessComError as error:
                ratings, note = None, f"Ratings unavailable: {error}"
            self._send(self.signals.done, (profile, ratings, note))

        except Exception as error:  # a worker thread must never die silently
            logging.getLogger(__name__).exception("Chess.com request failed")
            self._send(self.signals.failed, f"Unexpected error: {error}")

    def _send(self, signal, value) -> None:
        try:
            signal.emit(value)
        except RuntimeError:  # dialog was closed while the request was running
            pass


def _date(timestamp: int | None) -> str | None:
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
    except (OverflowError, OSError, ValueError):
        return None


def _n(value: int | None) -> str:
    return "-" if value is None else str(value)


def describe(profile: ChessComProfile, ratings: list[RatingLine] | None, note: str) -> str:
    lines = [f"{profile.title} {profile.username}" if profile.title else profile.username]
    for label, value in (
        ("Name", profile.name),
        ("Status", profile.status),
        ("Country", profile.country),
        ("Location", profile.location),
        ("Joined", _date(profile.joined)),
        ("Last online", _date(profile.last_online)),
        ("Followers", profile.followers),
        ("FIDE", profile.fide),
    ):
        if value is not None:
            lines.append(f"{label}: {value}")
    lines.append("")
    if ratings:
        lines.append("Chess.com ratings")
        for r in ratings:
            lines.append(
                f"{r.label:<16}{r.rating:>5}   best {_n(r.best)}   "
                f"W {_n(r.wins)}  L {_n(r.losses)}  D {_n(r.draws)}"
            )
    else:
        lines.append(note or "No ratings on this account.")
    lines += ["", "Public Chess.com data, read-only. It can lag behind the website."]
    return "\n".join(lines)


class ChessComDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Chess.com player lookup")
        self.resize(480, 360)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Chess.com username")
        self.name.setMaxLength(25)
        self.button = QPushButton("Look up")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        row = QHBoxLayout()
        row.addWidget(self.name, 1)
        row.addWidget(self.button)
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.output, 1)
        self.button.clicked.connect(self._lookup)  # Enter clicks it too (default button)

    def _lookup(self, _checked: bool = False) -> None:
        if not self.button.isEnabled():
            return
        try:
            username = chesscom.clean_username(self.name.text())
        except ChessComError as error:
            self.output.setPlainText(str(error))
            return
        self.button.setEnabled(False)
        self.output.setPlainText("Looking up...")
        signals = _Signals(self)
        signals.done.connect(self._show)
        signals.failed.connect(self._fail)
        QThreadPool.globalInstance().start(_Lookup(username, signals))

    def _show(self, result: tuple) -> None:
        profile, ratings, note = result
        self.output.setPlainText(describe(profile, ratings, note))
        self.button.setEnabled(True)

    def _fail(self, message: str) -> None:
        self.output.setPlainText(message)
        self.button.setEnabled(True)
