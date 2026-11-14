import chess
import pytest

from stockfih.chess.game import Game

SAMPLE = """[Event "Test"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0
"""


def play(g: Game, *ucis: str) -> None:
    for uci in ucis:
        m = chess.Move.from_uci(uci)
        assert g.move(m.from_square, m.to_square, m.promotion), uci


def test_import_then_step_with_undo_redo():
    g = Game()
    g.load_pgn(SAMPLE)
    assert g.board.fen() == chess.STARTING_FEN
    assert g.title() == "StockFih - Alice vs Bob"
    for _ in range(6):
        assert g.redo()
    assert not g.redo()
    assert g.history_text() == "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6"
    assert g.undo()


def test_export_keeps_names_and_unplayed_moves():
    g = Game()
    g.load_pgn(SAMPLE)
    text = g.export_pgn()  # still at the start: all moves are "upcoming"
    assert '[White "Alice"]' in text
    assert '[Black "Bob"]' in text
    assert "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0" in text


def test_export_played_game_has_result():
    g = Game()
    play(g, "f2f3", "e7e5", "g2g4", "d8h4")
    text = g.export_pgn()
    assert '[Result "0-1"]' in text
    assert "1. f3 e5 2. g4 Qh4#" in text


def test_custom_fen_round_trip():
    g = Game()
    g.board.set_fen("4k3/8/8/8/8/8/P7/4K3 w - - 0 1")
    play(g, "a2a3")
    g2 = Game()
    g2.load_pgn(g.export_pgn())
    assert g2.board.fen() == "4k3/8/8/8/8/8/P7/4K3 w - - 0 1"
    assert g2.redo()
    assert g2.board.fen() == g.board.fen()


def test_new_move_drops_imported_result():
    g = Game()
    g.load_pgn(SAMPLE)
    while g.redo():
        pass
    play(g, "b5a4")
    assert '[Result "*"]' in g.export_pgn()


def test_bad_pgn_is_rejected_and_game_untouched():
    g = Game()
    play(g, "e2e4")
    with pytest.raises(ValueError):
        g.load_pgn("")
    with pytest.raises(ValueError):
        g.load_pgn("1. e4 e5 2. Ke4")
    assert len(g.board.move_stack) == 1
