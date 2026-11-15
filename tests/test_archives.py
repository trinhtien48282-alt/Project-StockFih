from urllib.error import HTTPError

import pytest

from stockfih.chess.game import Game
from stockfih.services import chesscom
from stockfih.services.chesscom import ArchiveGame, ChessComError
from stockfih.ui.games_dialog import describe

PGN = """[Event "Live Chess"]
[Site "Chess.com"]
[Date "2026.05.25"]
[Round "-"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]
[CurrentPosition "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"]
[TimeControl "180"]
[Termination "Alice won by resignation"]

1. e4 {[%clk 0:03:00]} 1... e5 {[%clk 0:03:00]} 2. Nf3 {[%clk 0:02:59.9]} 2... Nc6 {[%clk 0:02:58]} 1-0
"""


def game(**changes):
    base = {
        "rules": "chess",
        "pgn": PGN,
        "white": {"username": "Alice", "rating": 1500},
        "black": {"username": "Bob", "rating": 1480},
        "time_class": "blitz",
        "end_time": 1000,
    }
    return {**base, **changes}


class _Reply:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size: int = -1) -> bytes:
        return self.body if size < 0 else self.body[:size]


def test_archives_newest_first_and_junk_dropped(monkeypatch):
    calls = []
    data = {
        "archives": [
            "https://api.chess.com/pub/player/erik/games/2026/09",
            "https://api.chess.com/pub/player/erik/games/2026/11",
            "https://api.chess.com/pub/player/erik/games/2025/12",
            "https://api.chess.com/pub/player/erik/games/2026/13",  # no such month
            "https://api.chess.com/pub/player/erik/games/2026/11",  # duplicate
            "nonsense",
            42,
        ]
    }
    monkeypatch.setattr(chesscom, "_get_json", lambda path, limit=0: calls.append(path) or data)
    assert chesscom.fetch_archives("Erik") == [(2026, 11), (2026, 9), (2025, 12)]
    assert calls == ["/player/erik/games/archives"]
    monkeypatch.setattr(chesscom, "_get_json", lambda path, limit=0: {"archives": "bad"})
    assert chesscom.fetch_archives("erik") == []


def test_archives_unknown_player(monkeypatch):
    monkeypatch.setattr(chesscom, "urlopen", lambda *a, **k: (_ for _ in ()).throw(HTTPError("u", 404, "m", {}, None)))
    with pytest.raises(ChessComError) as info:
        chesscom.fetch_archives("Nobody")
    assert 'No Chess.com player named "nobody"' in str(info.value)


def test_month_parsed_filtered_and_sorted(monkeypatch):
    calls = []
    data = {
        "games": [
            game(end_time=1000),
            game(end_time=3000, black={"username": "Cy", "rating": "high"}),
            game(rules="chess960"),  # variant: skipped
            game(pgn=None),
            game(pgn="   "),
            game(white={"rating": 1}),  # no username
            "junk",
            game(end_time=2000, time_class=7, pgn=PGN.replace('[Result "1-0"]', "")),
        ]
    }
    monkeypatch.setattr(chesscom, "_get_json", lambda path, limit=0: calls.append((path, limit)) or data)
    games = chesscom.fetch_month("Erik", 2026, 11)
    assert calls == [("/player/erik/games/2026/11", chesscom.MONTH_BYTES)]
    assert [g.end_time for g in games] == [3000, 2000, 1000]
    assert games[0].black_rating is None and games[0].result == "1-0"
    assert games[1].result is None and games[1].time_class is None  # bad values dropped
    assert (games[2].white, games[2].black_rating, games[2].time_class) == ("Alice", 1480, "blitz")


def test_month_rejects_bad_input_without_network(monkeypatch):
    monkeypatch.setattr(chesscom, "_get_json", lambda *a, **k: pytest.fail("network call"))
    for year, month in ((2026, 0), (2026, 13), (1800, 5), (10000, 5)):
        with pytest.raises(ChessComError):
            chesscom.fetch_month("erik", year, month)
    with pytest.raises(ChessComError):
        chesscom.fetch_month("bad name!", 2026, 5)


def test_oversize_response_is_refused(monkeypatch):
    monkeypatch.setattr(chesscom, "urlopen", lambda *a, **k: _Reply(b"{" + b" " * chesscom.MAX_BYTES))
    with pytest.raises(ChessComError) as info:
        chesscom.fetch_profile("erik")
    assert "too large" in str(info.value)


def test_chesscom_pgn_loads_and_steps():
    g = Game()
    g.load_pgn(PGN)  # clock comments and extra tags must not break import
    assert g.title() == "StockFih - Alice vs Bob"
    while g.redo():
        pass
    assert g.history_text() == "1. e4 e5 2. Nf3 Nc6"


def test_describe():
    full = ArchiveGame(PGN, "Alice", "Bob", 1500, 1480, "1-0", "blitz", 1700000000)
    assert describe(full) == "2023-11-14   Alice (1500) vs Bob (1480)   1-0   blitz"
    bare = ArchiveGame(PGN, "Alice", "Bob", None, None, None, None, None)
    assert describe(bare) == "?   Alice vs Bob   ?"
