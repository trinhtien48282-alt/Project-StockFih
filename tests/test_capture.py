import chess

from stockfih.chess.game import Game


def play(g: Game, *ucis: str) -> None:
    for uci in ucis:
        m = chess.Move.from_uci(uci)
        assert g.move(m.from_square, m.to_square, m.promotion), uci


def test_last_capture_after_move():
    g = Game()
    play(g, "e2e4", "d7d5")
    assert not g.last_capture
    play(g, "e4d5")
    assert g.last_capture


def test_last_capture_after_redo():
    g = Game()
    play(g, "e2e4", "d7d5", "e4d5")
    g.undo()
    g.undo()
    assert g.redo()
    assert not g.last_capture
    assert g.redo()
    assert g.last_capture
