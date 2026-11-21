import random

from stockfih.personality.cultural_rules import COUNTRIES, NAME_ORIGINS, CulturalSettings
from stockfih.personality.events import GameEvent

# Alien Mode (Phase 11.2): when the user has not chosen a valid country and name origin, and has
# turned the option on, StockFih talks in harmless nonsense. Nothing here translates anything,
# and no binary or code is used (binary can spell real words, which would be a translation).
# The one meaningful token is a move in standard notation, taken from a real event, so a line
# never claims anything the game did not do. Like the rest of the personality package it imports
# no engine or GUI, and it never touches a move.
# shortcut: fixed syllable list, no grammar. Extend SYLLABLES to change the sound.

SYLLABLES = (
    "BLORP", "ZIP", "ZAP", "ZOP", "WUB", "GLIB", "KREE",
    "MORB", "FLIX", "VRUM", "NYK", "QUOR", "TAZZ", "DROK",
)
MAX_SAN = 12  # longest move text accepted; real SAN is far shorter


def configured(settings: CulturalSettings) -> bool:
    # True when BOTH the country and the name origin are valid choices. The opt-in flag does not
    # matter here: this asks only whether the user has said who they are.
    country = (settings.country or "").strip().upper()
    origin = (settings.origin or "").strip().lower()
    return country in COUNTRIES and origin in NAME_ORIGINS


def alien_mode_on(enabled: bool, settings: CulturalSettings) -> bool:
    # Alien Mode runs only when the user turned it on AND has not configured identity.
    return enabled and not configured(settings)


def nonsense(rng: random.Random, low: int = 1, high: int = 3) -> str:
    # `low` to `high` random syllables, space-separated.
    return " ".join(rng.choice(SYLLABLES) for _ in range(rng.randint(low, high)))


def alien_line(rng: random.Random, san: str | None = None) -> str:
    # Nonsense only, or nonsense around one move in standard notation. ValueError for a move
    # text that is empty, too long or contains whitespace.
    if san is None:
        return nonsense(rng, 2, 4) + "."
    if not san or len(san) > MAX_SAN or any(c.isspace() for c in san):
        raise ValueError(f"Not a move in standard notation: {san!r}")
    return f"{nonsense(rng, 1, 2)}. {san}. {nonsense(rng, 1, 2)}."


def alien_for_events(events: list, rng: random.Random) -> str | None:
    # One alien line for the move in `events`, or None when there is no move (for example only
    # a game-level fact). Takes the move text from the event, so the line names the real move.
    moves = [event for event in events if isinstance(event, GameEvent)]
    if not moves:
        return None
    return alien_line(rng, moves[0].san)
