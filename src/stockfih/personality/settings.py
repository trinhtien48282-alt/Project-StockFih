import json
from dataclasses import asdict, dataclass

from stockfih.personality.commentary import MODES, PROFANITY_LEVELS
from stockfih.personality.cultural_rules import COUNTRIES, NAME_ORIGINS, CulturalSettings
from stockfih.personality.frequency import FREQUENCIES

# The user's personality settings for one profile. No GUI imports: the settings dialog edits
# these values and the profile database stores them as one JSON string. Stored text is
# external data, so loading never fails: anything unknown falls back to the default.
# Nothing here changes a chess move.

LANGUAGES = {"en": "English"}  # only languages that have dialogue files
MIN_ELO, MAX_ELO = 100, 3500  # range accepted for StockFih's assumed rating


@dataclass(frozen=True)
class PersonalitySettings:
    mode: str = "toxic_comedian"  # one of commentary.MODES
    frequency: str = "normal"  # one of frequency.FREQUENCIES
    profanity: str = "mild"  # one of PROFANITY_LEVELS
    elo_personality: bool = True  # rating-based attitude (tiers)
    cultural: bool = False  # opt-in identity jokes
    country: str = ""  # a COUNTRIES code, or "" for not set
    origin: str = ""  # a NAME_ORIGINS key, or "" for not set
    alien: bool = True  # Alien Mode while identity is not set
    language: str = "en"
    muted: bool = False
    # What the personality ASSUMES StockFih is rated, for the tier only. It is a personality
    # number, not a measurement. None = not set, so no tier is used.
    stockfih_elo: int | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @staticmethod
    def from_json(text: str) -> "PersonalitySettings":
        # Bad JSON, a wrong type or an unknown value gives the default for that field.
        default = PersonalitySettings()
        try:
            data = json.loads(text)
        except (TypeError, ValueError):
            return default
        if not isinstance(data, dict):
            return default

        def pick(key: str, allowed: tuple) -> str:
            value = data.get(key)
            return value if isinstance(value, str) and value in allowed else getattr(default, key)

        def flag(key: str) -> bool:
            value = data.get(key)
            return value if isinstance(value, bool) else getattr(default, key)

        elo = data.get("stockfih_elo")
        if isinstance(elo, bool) or not isinstance(elo, int) or not MIN_ELO <= elo <= MAX_ELO:
            elo = None
        return PersonalitySettings(
            mode=pick("mode", MODES),
            frequency=pick("frequency", tuple(FREQUENCIES)),
            profanity=pick("profanity", PROFANITY_LEVELS),
            elo_personality=flag("elo_personality"),
            cultural=flag("cultural"),
            country=pick("country", ("", *COUNTRIES)),
            origin=pick("origin", ("", *NAME_ORIGINS)),
            alien=flag("alien"),
            language=pick("language", tuple(LANGUAGES)),
            muted=flag("muted"),
            stockfih_elo=elo,
        )

    def to_cultural(self) -> CulturalSettings:
        return CulturalSettings(
            enabled=self.cultural, country=self.country or None, origin=self.origin or None
        )
