import chess
import pytest

from stockfih.chess.game import Game

CUSTOM = "4k3/8/8/8/8/8/P7/4K3 w - - 0 1"


def play(g: Game, *ucis: str) -> None:
    for uci in ucis:
        m = chess.Move.from_uci(uci)
        assert g.move(m.from_square, m.to_square, m.promotion), uci


def test_load_fen_starts_game_from_position():
    g = Game()
    play(g, "e2e4")
    g.load_fen(CUSTOM)
    assert g.board.fen() == CUSTOM
    assert not g.undo() and not g.redo()
    play(g, "a2a3")
    g.restart()
    assert g.board.fen() == CUSTOM
    g.new_game()
    assert g.board.fen() == chess.STARTING_FEN


def test_fen_round_trip_keeps_en_passant_and_castling():
    g = Game()
    play(g, "e2e4", "a7a6", "e4e5", "d7d5")
    fen = g.board.fen()
    g2 = Game()
    g2.load_fen(fen)
    assert g2.board.fen() == fen
    assert g2.board.ep_square == chess.D6
    assert g2.move(chess.E5, chess.D6)


def test_load_fen_resets_imported_headers():
    g = Game()
    g.load_pgn('[White "Alice"]\n[Black "Bob"]\n\n1. e4 e5 *\n')
    g.load_fen(CUSTOM)
    assert g.title() == "StockFih"


@pytest.mark.parametrize(
    "bad",
    [
        "garbage",
        "8/8/8/8/8/8/8/8 w - - 0 1",  # no kings
        "4k3/8/8/8/8/8/8/3KK3 w - - 0 1",  # two white kings
        "4k3/8/8/8/8/8/4R3/4K3 w - - 0 1",  # black king attacked, white to move
    ],
)
def test_bad_fen_is_rejected_and_game_untouched(bad):
    g = Game()
    play(g, "e2e4")
    with pytest.raises(ValueError):
        g.load_fen(bad)
    assert len(g.board.move_stack) == 1
