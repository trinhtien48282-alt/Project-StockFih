# Chess.com Published-Data API (PubAPI). Read-only public data, no login, no key.
# Docs: https://www.chess.com/news/view/published-data-api
# Endpoints used here: /player/{username}, /player/{username}/stats and /leaderboards.
# This module has no GUI imports. Every response is external data and is validated.
import json
import re
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "https://api.chess.com/pub"
# The docs ask for a recognizable user agent; add your contact info here if you want to.
USER_AGENT = "StockFih/0.1 (desktop chess app)"
TIMEOUT = 10  # seconds
MAX_BYTES = 2_000_000

_USERNAME = re.compile(r"[A-Za-z0-9_-]{1,25}")
_COUNTRY = re.compile(r"[A-Z]{2}")
_ORDER = ("chess_bullet", "chess_blitz", "chess_rapid", "chess_daily")
# /leaderboards key -> tab label. Order is display order.
BOARDS = (("live_bullet", "Bullet"), ("live_blitz", "Blitz"), ("live_rapid", "Rapid"))


class ChessComError(Exception):
    # The message is meant to be shown to the user as is.
    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ChessComProfile:
    username: str
    title: str | None
    name: str | None
    status: str | None
    country: str | None  # two-letter code
    location: str | None
    joined: int | None  # Unix seconds
    last_online: int | None  # Unix seconds
    followers: int | None
    fide: int | None


@dataclass(frozen=True)
class RatingLine:
    key: str  # PubAPI stats key, e.g. "chess_blitz"
    rating: int
    best: int | None
    wins: int | None
    losses: int | None
    draws: int | None

    @property
    def label(self) -> str:
        rules, _, time_class = self.key.partition("_")
        return time_class.capitalize() if rules == "chess" else f"{rules.capitalize()} {time_class}"


@dataclass(frozen=True)
class LeaderEntry:
    rank: int
    username: str
    score: int  # the board's rating
    title: str | None
    name: str | None
    country: str | None  # two-letter code
    wins: int | None
    losses: int | None
    draws: int | None


def clean_username(value: str) -> str:
    # Also keeps odd characters out of the request URL. PubAPI usernames work in lower case.
    name = value.strip()
    if not _USERNAME.fullmatch(name):
        raise ChessComError("Usernames use letters, digits, _ and -, up to 25 characters.")
    return name.lower()


def _http_message(code: int) -> str:
    if code == 404:
        return "Not found on Chess.com."
    if code == 410:
        return "Chess.com says this data is gone for good."
    if code == 429:
        return "Chess.com is rate limiting requests. Wait a bit and try again."
    return f"Chess.com returned HTTP {code}."


def _get_json(path: str) -> dict:
    request = Request(BASE + path, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read(MAX_BYTES)
    except HTTPError as error:
        raise ChessComError(_http_message(error.code), error.code) from None
    except OSError:  # no network, DNS failure, timeout
        raise ChessComError("Could not reach Chess.com. Check your internet connection.") from None
    try:
        data = json.loads(raw)
    except ValueError:
        data = None
    if not isinstance(data, dict):
        raise ChessComError("Chess.com sent data this app could not read.")
    return data


def _int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip() or None


def _country(value: object) -> str | None:
    # PubAPI sends a URL ending in the two-letter country code.
    text = _str(value)
    code = text.rsplit("/", 1)[-1].upper() if text else None
    return code if code and _COUNTRY.fullmatch(code) else None


def fetch_profile(username: str) -> ChessComProfile:
    name = clean_username(username)
    try:
        data = _get_json(f"/player/{name}")
    except ChessComError as error:
        if error.code == 404:
            raise ChessComError(f'No Chess.com player named "{name}".') from None
        raise
    return ChessComProfile(
        username=_str(data.get("username")) or name,
        title=_str(data.get("title")),
        name=_str(data.get("name")),
        status=_str(data.get("status")),
        country=_country(data.get("country")),
        location=_str(data.get("location")),
        joined=_int(data.get("joined")),
        last_online=_int(data.get("last_online")),
        followers=_int(data.get("followers")),
        fide=_int(data.get("fide")),
    )


def _rating_line(key: str, value: object) -> RatingLine | None:
    if "_" not in key or not isinstance(value, dict):
        return None
    last = value.get("last")
    rating = _int(last.get("rating")) if isinstance(last, dict) else None
    if rating is None:
        return None  # tactics, lessons, puzzle_rush and never-played types have no "last"
    best = value.get("best")
    record = value.get("record")
    record = record if isinstance(record, dict) else {}
    return RatingLine(
        key=key,
        rating=rating,
        best=_int(best.get("rating")) if isinstance(best, dict) else None,
        wins=_int(record.get("win")),
        losses=_int(record.get("loss")),
        draws=_int(record.get("draw")),
    )


def fetch_ratings(username: str) -> list[RatingLine]:
    # Only game types the player has actually played are present. May be empty.
    data = _get_json(f"/player/{clean_username(username)}/stats")
    lines = [line for key, value in data.items() if (line := _rating_line(str(key), value))]
    lines.sort(key=lambda line: (_ORDER.index(line.key) if line.key in _ORDER else len(_ORDER), line.key))
    return lines


def _leader(value: object) -> LeaderEntry | None:
    if not isinstance(value, dict):
        return None
    username, rank, score = _str(value.get("username")), _int(value.get("rank")), _int(value.get("score"))
    if username is None or rank is None or score is None:
        return None  # an entry without these cannot be shown honestly
    return LeaderEntry(
        rank=rank,
        username=username,
        score=score,
        title=_str(value.get("title")),
        name=_str(value.get("name")),
        country=_country(value.get("country")),
        wins=_int(value.get("win_count")),
        losses=_int(value.get("loss_count")),
        draws=_int(value.get("draw_count")),
    )


def fetch_leaderboards() -> dict[str, list[LeaderEntry]]:
    # One request returns every board (top 50 each). Keys are the BOARDS keys; a missing or
    # malformed board is an empty list. Sorted by the rank Chess.com sent.
    data = _get_json("/leaderboards")
    boards = {}
    for key, _label in BOARDS:
        raw = data.get(key)
        entries = [e for item in raw if (e := _leader(item))] if isinstance(raw, list) else []
        boards[key] = sorted(entries, key=lambda e: e.rank)
    return boards
