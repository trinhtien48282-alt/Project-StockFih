import random
from collections import deque
from dataclasses import dataclass

from stockfih.personality.commentary import Commentator
from stockfih.personality.events import EventKind, GameEvent
from stockfih.personality.game_events import FactEvent

# Decides WHEN the commentator speaks. It only gates lines that Commentator already chose:
# it never changes what is said, and it never touches a chess move.
# Plies are the game's own count (1 = White's first move), so the cooldown is measured in plies.


@dataclass(frozen=True)
class Frequency:
    min_gap: int  # plies that must pass after a line before the next ordinary line
    chance: float  # chance (0 to 1) that an ordinary event gets a line at all


# Silent is None: no lines at all, not even for game-ending events.
# Design numbers, tune later.
FREQUENCIES: dict[str, Frequency | None] = {
    "silent": None,
    "normal": Frequency(min_gap=6, chance=0.35),
    "chaotic": Frequency(min_gap=2, chance=0.75),
    "unhinged": Frequency(min_gap=0, chance=1.0),
}

# Game-ending facts always get a line (except on Silent), so a finished game is never silent.
ALWAYS = frozenset(
    {
        EventKind.CHECKMATE,
        EventKind.STALEMATE,
        EventKind.DRAW,
        EventKind.GAME_WON,
        EventKind.GAME_LOST,
        EventKind.GAME_DRAWN,
    }
)
HISTORY_SIZE = 12  # recent lines remembered; a remembered line is skipped while a fresh one fits


class Pacer:
    def __init__(
        self,
        commentator: Commentator,
        level: str = "normal",
        rng: random.Random | None = None,
    ) -> None:
        self.commentator = commentator
        self._rng = rng or random.Random()
        self._recent: deque[str] = deque(maxlen=HISTORY_SIZE)
        self._last_ply: int | None = None
        self.set_level(level)

    def set_level(self, level: str) -> None:
        # ValueError for an unknown level; the old level stays.
        if level not in FREQUENCIES:
            raise ValueError(f"Frequency must be one of {tuple(FREQUENCIES)}.")
        self.level = level

    def reset(self) -> None:
        # Call when a new game starts: the cooldown and the history belong to one game.
        self._recent.clear()
        self._last_ply = None

    def comment(self, events: list[GameEvent | FactEvent], ply: int) -> str | None:
        # One line, or None. `ply` is the game's current ply count.
        freq = FREQUENCIES[self.level]
        if freq is None:
            return None
        if not any(event.kind in ALWAYS for event in events):
            if self._last_ply is not None and ply - self._last_ply < freq.min_gap:
                return None
            if self._rng.random() >= freq.chance:
                return None
        line = self.commentator.comment(events, avoid=frozenset(self._recent))
        if line is None:
            return None
        self._recent.append(line)
        self._last_ply = ply
        return line
