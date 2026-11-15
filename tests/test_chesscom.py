from urllib.error import HTTPError, URLError

import pytest

from stockfih.services import chesscom
from stockfih.services.chesscom import ChessComError

PROFILE = {
    "username": "Erik",
    "title": "GM",
    "name": "Erik Allebest",
    "status": "premium",
    "country": "https://api.chess.com/pub/country/US",
    "location": "Utah",
    "joined": 1178556600,
    "last_online": 1500661803,
    "followers": 17,
    "fide": 2400,
}

STATS = {
    "chess_daily": {"last": {"rating": 1642, "rd": 58}, "best": {"rating": 2065}, "record": {"win": 177, "loss": 124, "draw": 21}},
    "chess_blitz": {"last": {"rating": 1500}},
    "chess_bullet": {"last": {"rating": 1400}, "record": {"win": "many"}},
    "chess_rapid": {"best": {"rating": 1800}},  # no "last": skipped
    "chess960_daily": {"last": {"rating": 1300}},
    "tactics": {"highest": {"rating": 2000}},
    "puzzle_rush": {"best": {"score": 30}},
}


class _Reply:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size: int = -1) -> bytes:
        return self.body if size < 0 else self.body[:size]


def _raise(error: BaseException):
    def fake(*args, **kwargs):
        raise error

    return fake


def test_username_validation():
    assert chesscom.clean_username("  Hikaru_1 ") == "hikaru_1"
    for bad in ("", "  ", "a b", "../x", "x/y", "x" * 26, "naïve"):
        with pytest.raises(ChessComError):
            chesscom.clean_username(bad)


def test_profile_parsed(monkeypatch):
    calls = []
    monkeypatch.setattr(chesscom, "_get_json", lambda path: calls.append(path) or PROFILE)
    p = chesscom.fetch_profile("Erik")
    assert calls == ["/player/erik"]
    assert (p.username, p.title, p.name, p.status) == ("Erik", "GM", "Erik Allebest", "premium")
    assert (p.country, p.location, p.joined, p.last_online) == ("US", "Utah", 1178556600, 1500661803)
    assert (p.followers, p.fide) == (17, 2400)


def test_profile_ignores_bad_types_and_missing_fields(monkeypatch):
    monkeypatch.setattr(
        chesscom,
        "_get_json",
        lambda path: {"followers": "lots", "joined": True, "country": "nonsense", "name": "  ", "fide": 1.5},
    )
    p = chesscom.fetch_profile("someone")
    assert p.username == "someone"  # falls back to the requested name
    assert (p.followers, p.joined, p.country, p.name, p.fide, p.title) == (None,) * 6


def test_ratings_parsed_and_ordered(monkeypatch):
    monkeypatch.setattr(chesscom, "_get_json", lambda path: STATS)
    lines = chesscom.fetch_ratings("erik")
    assert [l.key for l in lines] == ["chess_bullet", "chess_blitz", "chess_daily", "chess960_daily"]
    assert [l.label for l in lines] == ["Bullet", "Blitz", "Daily", "Chess960 daily"]
    daily = lines[2]
    assert (daily.rating, daily.best, daily.wins, daily.losses, daily.draws) == (1642, 2065, 177, 124, 21)
    assert lines[0].wins is None  # bad value is dropped, not guessed


def test_http_errors_become_messages(monkeypatch):
    for code, text in ((404, "Not found"), (410, "gone"), (429, "rate limiting"), (500, "HTTP 500")):
        monkeypatch.setattr(chesscom, "urlopen", _raise(HTTPError("u", code, "m", {}, None)))
        with pytest.raises(ChessComError) as info:
            chesscom.fetch_ratings("erik")
        assert text in str(info.value)
    monkeypatch.setattr(chesscom, "urlopen", _raise(HTTPError("u", 404, "m", {}, None)))
    with pytest.raises(ChessComError) as info:
        chesscom.fetch_profile("Nobody")
    assert 'No Chess.com player named "nobody"' in str(info.value)


def test_unreadable_data_and_network_failures_are_errors(monkeypatch):
    for body in (b"not json", b"[1, 2]", b"\xff\xfe"):
        monkeypatch.setattr(chesscom, "urlopen", lambda *a, **k: _Reply(body))
        with pytest.raises(ChessComError) as info:
            chesscom.fetch_profile("erik")
        assert "could not read" in str(info.value)
    for error in (URLError("down"), TimeoutError()):
        monkeypatch.setattr(chesscom, "urlopen", _raise(error))
        with pytest.raises(ChessComError) as info:
            chesscom.fetch_profile("erik")
        assert "reach" in str(info.value)
    monkeypatch.setattr(chesscom, "urlopen", lambda *a, **k: _Reply(b'{"username": "Erik"}'))
    assert chesscom.fetch_profile("erik").username == "Erik"
