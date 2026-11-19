import random
from pathlib import Path

import chess
import chess.polyglot


class OpeningBook:
    # Reads a standard Polyglot opening book (.bin). No book file ships with StockFih: you
    # point this at one. It has no GUI imports and never touches the caller's board.
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"Opening book not found: {self.path}")

    def pick(self, board: chess.Board, rng: random.Random) -> chess.Move | None:
        # A book move for this position, chosen at random by book weight, or None when the
        # position is not in the book or the file cannot be read. Only legal moves are
        # returned: the file is external data and a hash collision can give a wrong entry.
        # shortcut: the file is opened on every lookup (simple, no lock held on Windows).
        # Upgrade to one open reader if lookups ever show up in a profile.
        try:
            with chess.polyglot.open_reader(self.path) as reader:
                entries = [e for e in reader.find_all(board) if e.move in board.legal_moves]
        except (OSError, ValueError):  # unreadable or empty file
            return None
        if not entries:
            return None
        weights = [e.weight for e in entries]
        return rng.choices(entries, weights=weights if any(weights) else None)[0].move
