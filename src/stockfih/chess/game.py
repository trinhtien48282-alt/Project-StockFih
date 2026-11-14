import re

import chess

from stockfih.chess import pgn as pgn_io

# PGN date: YYYY.MM.DD, any part may be ? when unknown.
_DATE = re.compile(r"(\d{4}|\?{4})\.(0[1-9]|1[0-2]|\?\?)\.(0[1-9]|[12]\d|3[01]|\?\?)")
_INFO_DEFAULTS = {"White": "?", "Black": "?", "Event": "?", "Date": "????.??.??"}


def _clean(value: str) -> str:
    # One line, no quotes or backslashes (they would break the PGN header).
    value = "".join(c for c in value if c not in '"\\')
    return " ".join(value.split()) or "?"


class Game:
    def __init__(self) -> None:
        self.board = chess.Board()
        self._redo: list[chess.Move] = []
        self.headers = pgn_io.default_headers()
        self.last_capture = False  # did the latest move played or redone capture?

    def outcome(self) -> chess.Outcome | None:
        # Mate, stalemate, insufficient material, 75-move, fivefold: python-chess ends these itself.
        # Threefold and 50-move are claims in real chess. We apply them automatically, but
        # only once the position has actually occurred / the clock has actually reached it.
        out = self.board.outcome()
        if out is not None:
            return out
        if self.board.is_repetition(3):
            return chess.Outcome(chess.Termination.THREEFOLD_REPETITION, None)
        if self.board.is_fifty_moves():
            return chess.Outcome(chess.Termination.FIFTY_MOVES, None)
        return None

    def targets(self, square: chess.Square) -> list[chess.Square]:
        if self.outcome() is not None:
            return []
        return [m.to_square for m in self.board.legal_moves if m.from_square == square]

    def needs_promotion(self, from_sq: chess.Square, to_sq: chess.Square) -> bool:
        piece = self.board.piece_at(from_sq)
        return bool(piece and piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in (0, 7))

    def move(
        self,
        from_sq: chess.Square,
        to_sq: chess.Square,
        promotion: chess.PieceType | None = None,
    ) -> bool:
        move = chess.Move(from_sq, to_sq, promotion=promotion)
        if self.outcome() is not None or move not in self.board.legal_moves:
            return False
        self.last_capture = self.board.is_capture(move)
        self.board.push(move)
        self._redo.clear()
        self.headers.pop("Result", None)  # an imported result no longer applies
        return True

    def undo(self) -> bool:
        if not self.board.move_stack:
            return False
        self._redo.append(self.board.pop())
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        move = self._redo.pop()
        self.last_capture = self.board.is_capture(move)
        self.board.push(move)
        return True

    def new_game(self) -> None:
        self.board = chess.Board()
        self._redo.clear()
        self.headers = pgn_io.default_headers()

    def restart(self) -> None:
        # Back to this game's starting position (differs from new_game once custom FEN lands in 3.2).
        self.board = self.board.root()
        self._redo.clear()

    def load_fen(self, fen: str) -> None:
        # Raises ValueError and leaves this game untouched if the FEN is bad or the position illegal.
        board = chess.Board(fen)
        status = board.status()
        if status != chess.STATUS_VALID:
            problems = ", ".join(f.name.replace("_", " ").lower() for f in chess.Status if f in status)
            raise ValueError(f"Invalid position: {problems}.")
        self.board = board
        self._redo.clear()
        self.headers = pgn_io.default_headers()

    def load_pgn(self, text: str) -> None:
        # Raises ValueError and leaves this game untouched if the PGN is bad.
        board, moves, headers = pgn_io.import_pgn(text)
        self.board = board
        self._redo = moves[::-1]  # step through the game with redo / undo
        self.headers = headers

    def result(self) -> str:
        out = self.outcome()
        if out is not None and not self._redo:
            return out.result()
        return self.headers.get("Result", "*")

    def export_pgn(self) -> str:
        return pgn_io.export_pgn(self.board, self._redo[::-1], self.headers, self.result())

    def info(self) -> dict[str, str]:
        # The editable game details.
        return {key: self.headers.get(key, default) for key, default in _INFO_DEFAULTS.items()}

    def set_info(self, values: dict[str, str]) -> None:
        # Raises ValueError and changes nothing if the date is malformed.
        date = _clean(values["Date"])
        if date == "?":
            date = _INFO_DEFAULTS["Date"]
        if not _DATE.fullmatch(date):
            raise ValueError("Date must look like 2026.11.14 (use ? for unknown parts).")
        for key in ("White", "Black", "Event"):
            self.headers[key] = _clean(values[key])
        self.headers["Date"] = date

    def extra_info(self) -> dict[str, str]:
        # Read-only details. Opening and ECO appear only if the imported PGN carried them.
        result = self.result()
        extra = {"Result": "unfinished" if result == "*" else result}
        for key in ("Opening", "ECO"):
            if key in self.headers:
                extra[key] = self.headers[key]
        return extra

    def title(self) -> str:
        white, black = self.headers.get("White", "?"), self.headers.get("Black", "?")
        return "StockFih" if white == black == "?" else f"StockFih - {white} vs {black}"

    def history_text(self) -> str:
        return self.board.root().variation_san(self.board.move_stack)

    def status(self) -> str:
        out = self.outcome()
        if out is None:
            side = "White" if self.board.turn == chess.WHITE else "Black"
            return f"{side} to move" + (" - check" if self.board.is_check() else "")
        if out.termination == chess.Termination.CHECKMATE:
            return f"Checkmate - {'White' if out.winner == chess.WHITE else 'Black'} wins"
        return "Draw - " + out.termination.name.replace("_", " ").capitalize()

    @property
    def last_move(self) -> chess.Move | None:
        return self.board.move_stack[-1] if self.board.move_stack else None

    def check_square(self) -> chess.Square | None:
        return self.board.king(self.board.turn) if self.board.is_check() else None
