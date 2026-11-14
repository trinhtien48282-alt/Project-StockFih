import chess

from stockfih.chess.game import Game


def fresh(fen: str) -> Game:
    g = Game()
    g.board.set_fen(fen)
    return g


def play(g: Game, *ucis: str) -> None:
    for uci in ucis:
        m = chess.Move.from_uci(uci)
        assert g.move(m.from_square, m.to_square, m.promotion), uci


def test_castle_kingside_and_queenside():
    g = fresh("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    assert g.move(chess.E1, chess.G1)
    assert g.board.piece_at(chess.F1).symbol() == "R"
    g = fresh("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    assert g.move(chess.E1, chess.C1)
    assert g.board.piece_at(chess.D1).symbol() == "R"


def test_castle_through_attacked_square_illegal():
    g = fresh("4k3/8/8/8/8/8/5r2/R3K2R w KQ - 0 1")
    assert not g.move(chess.E1, chess.G1)
    assert g.move(chess.E1, chess.C1)


def test_en_passant():
    g = fresh("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
    assert g.move(chess.E5, chess.D6)
    assert g.board.piece_at(chess.D5) is None
    assert g.board.piece_at(chess.D6).symbol() == "P"


def test_promotion_requires_piece_choice():
    g = fresh("8/P7/8/8/8/8/8/k6K w - - 0 1")
    assert g.needs_promotion(chess.A7, chess.A8)
    assert not g.move(chess.A7, chess.A8)
    assert g.move(chess.A7, chess.A8, chess.KNIGHT)
    assert g.board.piece_at(chess.A8).symbol() == "N"


def test_checkmate_and_game_over_blocks_moves():
    g = Game()
    play(g, "f2f3", "e7e5", "g2g4", "d8h4")
    out = g.outcome()
    assert out.termination == chess.Termination.CHECKMATE
    assert out.winner == chess.BLACK
    assert not g.move(chess.E2, chess.E4)
    assert g.targets(chess.E2) == []


def test_stalemate():
    g = fresh("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert g.outcome().termination == chess.Termination.STALEMATE


def test_insufficient_material():
    g = fresh("8/8/8/4k3/8/8/4K3/8 w - - 0 1")
    assert g.outcome().termination == chess.Termination.INSUFFICIENT_MATERIAL


def test_threefold_repetition():
    g = Game()
    cycle = ("g1f3", "g8f6", "f3g1", "f6g8")
    play(g, *cycle, *cycle)
    assert g.outcome().termination == chess.Termination.THREEFOLD_REPETITION


def test_fifty_move_rule():
    g = fresh("4k3/8/8/8/8/8/8/R3K3 w - - 100 80")
    assert g.outcome().termination == chess.Termination.FIFTY_MOVES