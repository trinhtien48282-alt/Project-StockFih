import math
from enum import Enum

# Maps the rating gap between the player and StockFih to a personality tier. Like the rest of
# the personality package it imports no engine and no GUI, and it never touches a move.
# It invents no rating: both numbers come from the caller, and a missing one gives no tier.
# The thresholds are design numbers from the roadmap, not official chess categories.


class Tier(Enum):
    # Values match the tier keys planned for dialogue.json (Phase 10.3).
    DOMINANT = "dominant"  # player far weaker
    COCKY = "cocky"
    RIVAL = "rival"
    THREATENED = "threatened"
    EXISTENTIAL_CRISIS = "existential_crisis"  # player far stronger


# difference = player - stockfih. A gap at or below the limit belongs to that tier.
DOMINANT_MAX = -300
COCKY_MAX = -100
# Rival is everything above COCKY_MAX and below THREATENED_MIN; THREATENED_MIN itself is Threatened.
THREATENED_MIN = 100
EXISTENTIAL_MIN = 300


def _check(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive number.")
    return float(value)


def rating_difference(player_elo: float, stockfih_elo: float) -> float:
    # Positive: the player is rated higher. ValueError for a non-positive or non-finite rating.
    return _check("Player rating", player_elo) - _check("StockFih rating", stockfih_elo)


def tier_for_difference(difference: float) -> Tier:
    if difference <= DOMINANT_MAX:
        return Tier.DOMINANT
    if difference <= COCKY_MAX:
        return Tier.COCKY
    if difference < THREATENED_MIN:
        return Tier.RIVAL
    if difference < EXISTENTIAL_MIN:
        return Tier.THREATENED
    return Tier.EXISTENTIAL_CRISIS


def tier_for(player_elo: float | None, stockfih_elo: float | None) -> Tier | None:
    # None when either rating is unknown (for example a player's still-provisional rating).
    # Callers then use the neutral commentary instead of guessing a tier.
    if player_elo is None or stockfih_elo is None:
        return None
    return tier_for_difference(rating_difference(player_elo, stockfih_elo))
