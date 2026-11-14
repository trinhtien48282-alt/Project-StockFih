import chess

from stockfih.chess.game import Game


def play(g: Game, *ucis: str) -> None:
    for uci in ucis:
        m = chess.Move.from_uci(uci)
        assert g.move(m.from_square, m.to_square, m.promotion), uci


def test_undo_redo():
    g = Game()
    play(g, "e2e4", "e7e5")
    assert g.undo() and g.undo()
    assert not g.undo()
    assert g.board.fen() == chess.STARTING_FEN
    assert g.redo() and g.redo()
    assert not g.redo()
    assert g.board.piece_at(chess.E5).symbol() == "p"


def test_new_move_clears_redo():
    g = Game()
    play(g, "e2e4")
    g.undo()
    play(g, "d2d4")
    assert not g.redo()


def test_undo_after_checkmate_resumes_play():
    g = Game()
    play(g, "f2f3", "e7e5", "g2g4", "d8h4")
    assert g.outcome() is not None
    assert g.undo()
    assert g.outcome() is None
    play(g, "d8h4")
    assert g.outcome() is not None


def test_restart_and_new_game():
    g = Game()
    g.board.set_fen("4k3/8/8/8/8/8/8/R3K3 w Q - 0 1")
    start = g.board.fen()
    play(g, "a1a2")
    g.undo()
    g.restart()
    assert g.board.fen() == start
    assert not g.redo()
    play(g, "a1a2")
    g.new_game()
    assert g.board.fen() == chess.STARTING_FEN
    assert not g.undo() and not g.redo()


def test_history_text():
    g = Game()
    assert g.history_text() == ""
    play(g, "e2e4", "e7e5", "g1f3")
    assert g.history_text() == "1. e4 e5 2. Nf3"


def test_history_text_black_start():
    g = Game()
    g.board.set_fen("4k3/8/8/8/8/8/P7/4K3 b - - 0 7")
    play(g, "e8d8")
    assert g.history_text() == "7...Kd8"


def test_status():
    g = Game()
    assert g.status() == "White to move"
    play(g, "f2f3", "e7e5", "g2g4", "d8h4")
    assert g.status() == "Checkmate - Black wins"
    g.board.set_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert g.status() == "Draw - Stalemate"
    g.board.set_fen("4k3/8/8/8/8/8/4R3/4K3 b - - 0 1")
    assert g.status() == "Black to move - check"
