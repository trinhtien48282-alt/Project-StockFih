import gzip
from http.client import IncompleteRead

import pytest

from stockfih.services import chesscom
from stockfih.services.chesscom import ChessComError


class _Reply:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size: int = -1) -> bytes:
        return self.body if size < 0 else self.body[:size]


def _serve(monkeypatch, body: bytes) -> list:
    seen = []

    def fake(request, timeout):
        seen.append(request.get_header("Accept-encoding"))
        return _Reply(body)

    monkeypatch.setattr(chesscom, "urlopen", fake)
    return seen


def test_gzip_is_requested_and_unpacked(monkeypatch):
    seen = _serve(monkeypatch, gzip.compress(b'{"username": "Erik"}'))
    assert chesscom.fetch_profile("erik").username == "Erik"
    assert seen == ["gzip"]


def test_gzip_bomb_is_refused(monkeypatch):
    _serve(monkeypatch, gzip.compress(b" " * (chesscom.MAX_BYTES + 10)))
    with pytest.raises(ChessComError) as info:
        chesscom.fetch_profile("erik")
    assert "too large" in str(info.value)


def test_corrupt_gzip_is_an_error(monkeypatch):
    _serve(monkeypatch, b"\x1f\x8bgarbage")
    with pytest.raises(ChessComError) as info:
        chesscom.fetch_profile("erik")
    assert "could not read" in str(info.value)


def test_connection_cut_mid_reply_is_an_error(monkeypatch):
    def fake(*args, **kwargs):
        raise IncompleteRead(b"")

    monkeypatch.setattr(chesscom, "urlopen", fake)
    with pytest.raises(ChessComError) as info:
        chesscom.fetch_profile("erik")
    assert "reach" in str(info.value)
