import chess
import pytest

from stockfih.chess.game import Game


def play(g: Game, *ucis: str) -> None:
    for uci in ucis:
        m = chess.Move.from_uci(uci)
        assert g.move(m.from_square, m.to_square, m.promotion), uci


def values(**changes: str) -> dict[str, str]:
    base = {"White": "?", "Black": "?", "Event": "?", "Date": "????.??.??"}
    return {**base, **changes}


def test_defaults():
    info = Game().info()
    assert info["White"] == "?" and info["Black"] == "?"
    assert info["Event"] == "StockFih game"


def test_set_info_reaches_title_and_pgn():
    g = Game()
    g.set_info(values(White="Akarui", Black="StockFih", Event="Casual", Date="2026.11.14"))
    assert g.title() == "StockFih - Akarui vs StockFih"
    text = g.export_pgn()
    assert '[White "Akarui"]' in text
    assert '[Black "StockFih"]' in text
    assert '[Date "2026.11.14"]' in text


@pytest.mark.parametrize("bad", ["2026-11-14", "2026.13.01", "2026.11.32", "tomorrow"])
def test_bad_date_is_rejected_and_nothing_changes(bad):
    g = Game()
    with pytest.raises(ValueError):
        g.set_info(values(White="Akarui", Date=bad))
    assert g.info()["White"] == "?"


def test_partial_and_empty_dates_and_names():
    g = Game()
    g.set_info(values(White="  ", Date="2026.??.??"))
    assert g.info()["White"] == "?"
    assert g.info()["Date"] == "2026.??.??"
    g.set_info(values(Date=""))
    assert g.info()["Date"] == "????.??.??"


def test_quotes_and_backslashes_are_stripped():
    g = Game()
    g.set_info(values(White='Al"ice\\'))
    assert g.info()["White"] == "Alice"


def test_extra_info_result_and_opening_only_when_present():
    g = Game()
    assert g.extra_info() == {"Result": "unfinished"}
    play(g, "f2f3", "e7e5", "g2g4", "d8h4")
    assert g.extra_info()["Result"] == "0-1"
    g.load_pgn('[ECO "C60"]\n[Opening "Ruy Lopez"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 *\n')
    assert g.extra_info()["Opening"] == "Ruy Lopez"
    assert g.extra_info()["ECO"] == "C60"
