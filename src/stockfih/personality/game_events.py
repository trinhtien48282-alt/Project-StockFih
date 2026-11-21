from dataclasses import dataclass

from stockfih.personality.events import EventKind
from stockfih.personality.judgement import MATE_BOUND
from stockfih.profiles.statistics import outcome_for

# Game-level facts for the commentary. Like events.py and judgement.py, this module imports no
# engine and no GUI, and it never invents a value: a missing input gives None.

SWING_CP = 200  # evaluation change that counts as a major swing (a design number, tune later)
OPENING_MAX_CHARS = 80  # PGN headers are external data: longer names are refused, not cut


@dataclass(frozen=True)
class FactEvent:
    kind: EventKind
    text: str = ""  # MAJOR_SWING: "white" or "black" (who gained). OPENING: the name.
    country: str = ""  # IDENTITY_*: display names taken from fixed tables, never typed text
    origin: str = ""


def major_swing(white_before: int, white_after: int) -> FactEvent | None:
    # Both scores are White's point of view, centipawns, from the same engine and depth.
    # Mate scores are skipped: a swing into mate is already a judgement, not a swing.
    if abs(white_before) >= MATE_BOUND or abs(white_after) >= MATE_BOUND:
        return None
    change = white_after - white_before
    if abs(change) < SWING_CP:
        return None
    return FactEvent(EventKind.MAJOR_SWING, "white" if change > 0 else "black")


def result_for_player(result: str, player_color: str) -> FactEvent | None:
    # player_color: "white" or "black". Unfinished games ("*") and unknown colours give None.
    # Uses the same rule as the profile statistics, so the two never disagree.
    kinds = {
        "win": EventKind.GAME_WON,
        "loss": EventKind.GAME_LOST,
        "draw": EventKind.GAME_DRAWN,
    }
    outcome = outcome_for(result, player_color)
    return FactEvent(kinds[outcome]) if outcome in kinds else None


def opening_from_headers(headers: dict[str, str]) -> FactEvent | None:
    # Uses only the Opening header, then the ECO code. Nothing is looked up or guessed.
    for key in ("Opening", "ECO"):
        text = " ".join(str(headers.get(key, "")).split())
        if text and len(text) <= OPENING_MAX_CHARS:
            return FactEvent(EventKind.OPENING, text)
    return None
