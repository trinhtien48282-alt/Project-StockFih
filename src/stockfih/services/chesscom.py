# Chess.com Published-Data API (PubAPI). Read-only public data, no login, no key.
# Docs: https://www.chess.com/news/view/published-data-api
# Endpoints used here: /player/{username}, /player/{username}/stats, /leaderboards,
# /player/{username}/games/archives and /player/{username}/games/{YYYY}/{MM}.
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
# shortcut: a very busy month (tens of MB) is refused, not paged. Upgrade if people hit it.
MONTH_BYTES = 30_000_000

_USERNAME = re.compile(r"[A-Za-z0-9_-]{1,25}")
_COUNTRY = re.compile(r"[A-Z]{2}")
_RESULT = re.compile(r'\[Result "(1-0|0-1|1/2-1/2|\*)"\]')
_ARCHIVE = re.compile(r"/games/(\d{4})/(0[1-9]|1[0-2])$")
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


@dataclass(frozen=True)
class ArchiveGame:
    pgn: str
    white: str
    black: str
    white_rating: int | None
    black_rating: int | None
    result: str | None  # "1-0", "0-1", "1/2-1/2" or "*", read from the PGN header
    time_class: str | None  # "bullet", "blitz", "rapid", "daily"
    end_time: int | None  # Unix seconds


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


def _get_json(path: str, limit: int = MAX_BYTES) -> dict:
    request = Request(BASE + path, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read(limit + 1)
    except HTTPError as error:
        raise ChessComError(_http_message(error.code), error.code) from None
    except OSError:  # no network, DNS failure, timeout
        raise ChessComError("Could not reach Chess.com. Check your internet connection.") from None
    if len(raw) > limit:
        raise ChessComError("That Chess.com response is too large to load.")
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


def fetch_archives(username: str) -> list[tuple[int, int]]:
    # Months (year, month) in which the player has public games, newest first. May be empty.
    name = clean_username(username)
    try:
        data = _get_json(f"/player/{name}/games/archives")
    except ChessComError as error:
        if error.code == 404:
            raise ChessComError(f'No Chess.com player named "{name}".') from None
        raise
    raw = data.get("archives")
    months = set()
    for url in raw if isinstance(raw, list) else []:
        match = _ARCHIVE.search(url) if isinstance(url, str) else None
        if match:
            months.add((int(match[1]), int(match[2])))
    return sorted(months, reverse=True)


def _side(value: object) -> tuple[str | None, int | None]:
    if not isinstance(value, dict):
        return None, None
    return _str(value.get("username")), _int(value.get("rating"))


def _archive_game(value: object) -> ArchiveGame | None:
    # shortcut: standard chess only. Variants (chess960, crazyhouse...) are skipped, not loaded.
    if not isinstance(value, dict) or value.get("rules") != "chess":
        return None
    pgn = value.get("pgn")
    white, white_rating = _side(value.get("white"))
    black, black_rating = _side(value.get("black"))
    if not isinstance(pgn, str) or not pgn.strip() or white is None or black is None:
        return None
    result = _RESULT.search(pgn)
    return ArchiveGame(
        pgn=pgn,
        white=white,
        black=black,
        white_rating=white_rating,
        black_rating=black_rating,
        result=result[1] if result else None,
        time_class=_str(value.get("time_class")),
        end_time=_int(value.get("end_time")),
    )


def fetch_month(username: str, year: int, month: int) -> list[ArchiveGame]:
    # One month of a player's finished standard games, newest first. May be empty.
    if not (1970 <= year <= 9999 and 1 <= month <= 12):
        raise ChessComError("That is not a valid month.")
    path = f"/player/{clean_username(username)}/games/{year:04d}/{month:02d}"
    raw = _get_json(path, MONTH_BYTES).get("games")
    games = [g for item in raw if (g := _archive_game(item))] if isinstance(raw, list) else []
    games.sort(key=lambda g: g.end_time or 0, reverse=True)
    return games
