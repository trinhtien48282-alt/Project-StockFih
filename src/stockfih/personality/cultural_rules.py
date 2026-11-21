from dataclasses import dataclass

from stockfih.personality.events import EventKind
from stockfih.personality.game_events import FactEvent

# Opt-in commentary about two settings the USER chose: a country and a name origin. Like the
# rest of the personality package it imports no engine and no GUI, and it never touches a move.
#
# Rules this module keeps:
#   * Nothing is inferred. A username is never an input, and a name proves nothing about anyone.
#   * Off unless the user turned it on, and silent when either setting is missing or unknown.
#   * It compares the two settings only. Match or mismatch says something about the settings
#     ("unexpected combination"), never about the person, and never states a stereotype.
# shortcut: a small starter table. A country or origin outside it gives no comment at all.
# Add rows here to extend it; nothing else changes.

COUNTRIES = {  # ISO 3166 alpha-2 code -> display name (the same codes Chess.com profiles use)
    "BR": "Brazil",
    "CN": "China",
    "DE": "Germany",
    "ES": "Spain",
    "FR": "France",
    "GB": "United Kingdom",
    "IT": "Italy",
    "JP": "Japan",
    "KR": "South Korea",
    "MX": "Mexico",
    "PT": "Portugal",
    "RU": "Russia",
    "US": "United States",
    "VN": "Vietnam",
}

# key -> (display label, countries where that naming tradition is the local one)
NAME_ORIGINS = {
    "chinese": ("Chinese", frozenset({"CN"})),
    "english": ("English", frozenset({"GB", "US"})),
    "french": ("French", frozenset({"FR"})),
    "german": ("German", frozenset({"DE"})),
    "italian": ("Italian", frozenset({"IT"})),
    "japanese": ("Japanese", frozenset({"JP"})),
    "korean": ("Korean", frozenset({"KR"})),
    "portuguese": ("Portuguese", frozenset({"BR", "PT"})),
    "russian": ("Russian", frozenset({"RU"})),
    "spanish": ("Spanish", frozenset({"ES", "MX"})),
    "vietnamese": ("Vietnamese", frozenset({"VN"})),
}


@dataclass(frozen=True)
class CulturalSettings:
    enabled: bool = False  # opt-in: off until the user turns it on
    country: str | None = None  # a COUNTRIES code, as the user picked it
    origin: str | None = None  # a NAME_ORIGINS key, as the user picked it


def identity_event(settings: CulturalSettings) -> FactEvent | None:
    # IDENTITY_MATCH or IDENTITY_MISMATCH, or None when the feature is off or a setting is
    # missing or not in the tables. Settings are stored data, so unknown values are ignored,
    # not guessed at.
    if not settings.enabled:
        return None
    country = (settings.country or "").strip().upper()
    origin = (settings.origin or "").strip().lower()
    if country not in COUNTRIES or origin not in NAME_ORIGINS:
        return None
    label, homes = NAME_ORIGINS[origin]
    kind = EventKind.IDENTITY_MATCH if country in homes else EventKind.IDENTITY_MISMATCH
    return FactEvent(kind, country=COUNTRIES[country], origin=label)
