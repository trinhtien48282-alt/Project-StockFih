# StockFih rating: plain Elo, kept inside this app only. It is NOT a Chess.com or FIDE rating.
#
#   expected = 1 / (1 + 10 ** ((opponent - rating) / 400))
#   new      = rating + K * (score - expected)      score: win 1, draw 0.5, loss 0
#
# K is 40 for a profile's first 10 rated games (settles fast), then 20.
# Everyone starts at START. That number is a starting point, not a measured strength, so the
# rating is hidden until PROVISIONAL_GAMES rated games exist (see current / peak).
from dataclasses import dataclass

START = 1200.0
PROVISIONAL_GAMES = 5
NEW_GAMES = 10
K_NEW = 40.0
K_NORMAL = 20.0
SCORES = {"win": 1.0, "draw": 0.5, "loss": 0.0}


@dataclass(frozen=True)
class RatingChange:
    id: int
    played: str
    opponent: float
    score: float
    before: float
    after: float


def expected(rating: float, opponent: float) -> float:
    return 1 / (1 + 10 ** ((opponent - rating) / 400))


def update(rating: float, opponent: float, score: float, games: int) -> float:
    # games = rated games the profile has already played.
    k = K_NEW if games < NEW_GAMES else K_NORMAL
    return rating + k * (score - expected(rating, opponent))


def current(history: list[RatingChange]) -> float | None:
    # history is oldest first. None while still provisional.
    return history[-1].after if len(history) >= PROVISIONAL_GAMES else None


def peak(history: list[RatingChange]) -> float | None:
    # Highest rating since it became visible.
    visible = history[PROVISIONAL_GAMES - 1 :]
    return max(c.after for c in visible) if visible else None
