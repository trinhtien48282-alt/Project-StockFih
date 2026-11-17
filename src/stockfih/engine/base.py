from typing import Protocol

import chess


class Engine(Protocol):
    # Anything that can pick a move. The GUI will talk to this, never to a concrete engine.
    def choose_move(self, board: chess.Board) -> chess.Move:
        # Must return a legal move and leave `board` unchanged. ValueError if there is none.
        ...
