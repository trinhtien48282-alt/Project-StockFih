from enum import Enum

import chess

from stockfih.personality.events import EventKind, GameEvent
from stockfih.personality.game_events import FactEvent

# StockFih's ego: a temporary number for ONE game. It is not a rating and never replaces the
# real ELO tier (elo_personality.py). It moves only on facts that were measured: judgements
# (judgement.py) and major evaluation swings (game_events.py). Like the rest of the
# personality package it imports no engine and no GUI, and it never touches a move.
# All numbers are design numbers, tune later.
#
# shortcut: only bad moves and big swings move the ego. A "strong move" cannot be claimed
# without a measurement (BRILLIANT is not defined), so none is rewarded yet.
# A blunder that causes a swing counts twice (judgement, then swing). That is on purpose:
# it makes a collapse feel fast. Upgrade if it skews the mood.

START = 70
MIN, MAX = 0, 100
CONFIDENT_MIN = 60  # at or above: confident
SUSPICIOUS_MIN = 30  # at or above (and below CONFIDENT_MIN): suspicious. Below: making excuses.

# Size of the change for a judgement. The sign depends on who moved: a mistake by the player
# lifts the ego, the same mistake by StockFih lowers it.
JUDGEMENT = {
    EventKind.INACCURACY: 3,
    EventKind.MISTAKE: 6,
    EventKind.BLUNDER: 12,
    EventKind.MISSED_WIN: 12,
}
SWING = 8  # a major swing toward StockFih adds this, toward the player subtracts it


class Mood(Enum):
    # Values are meant to be dialogue keys (Phase 10.3).
    CONFIDENT = "confident"
    SUSPICIOUS = "suspicious"
    EXCUSES = "excuses"


class Ego:
    def __init__(self, stockfih_color: chess.Color = chess.BLACK) -> None:
        self.stockfih_color = stockfih_color
        self.value = START

    def reset(self, stockfih_color: chess.Color | None = None) -> None:
        # Call when a new game starts. The ego belongs to one game.
        if stockfih_color is not None:
            self.stockfih_color = stockfih_color
        self.value = START

    @property
    def mood(self) -> Mood:
        if self.value >= CONFIDENT_MIN:
            return Mood.CONFIDENT
        if self.value >= SUSPICIOUS_MIN:
            return Mood.SUSPICIOUS
        return Mood.EXCUSES

    def _add(self, change: int) -> None:
        self.value = max(MIN, min(MAX, self.value + change))

    def update(self, event: GameEvent | FactEvent) -> None:
        # Events that carry no measured fact for the ego are ignored.
        if isinstance(event, FactEvent):
            if event.kind is EventKind.MAJOR_SWING and event.text in ("white", "black"):
                gained = chess.WHITE if event.text == "white" else chess.BLACK
                self._add(SWING if gained == self.stockfih_color else -SWING)
            return
        size = JUDGEMENT.get(event.kind)
        if size is not None:
            self._add(size if event.by == "player" else -size)
