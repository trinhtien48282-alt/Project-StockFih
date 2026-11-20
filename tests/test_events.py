import chess
import pytest

from stockfih.personality.events import EventKind, events_for_move

K = EventKind


def kinds(events):
    return [e.kind for e in events]


def play(fen, uci, by="player"):
    board = chess.Board(fen)
    return events_for_move(board, chess.Move.from_uci(uci), by)


def test_plain_move():
    events = events_for_move(chess.Board(), chess.Move.from_uci("e2e4"), "player")
    assert kinds(events) == [K.MOVE]
    assert events[0].san == "e4" and events[0].ply == 1 and events[0].color == chess.WHITE
    assert events[0].by == "player"


def test_ply_and_color_of_black_move():
    board = chess.Board()
    board.push_san("e4")
    event = events_for_move(board, chess.Move.from_uci("e7e5"), "stockfih")[0]
    assert event.ply == 2 and event.color == chess.BLACK and event.by == "stockfih"


def test_capture_names_the_victim():
    board = chess.Board()
    for san in ("e4", "d5"):
        board.push_san(san)
    events = events_for_move(board, chess.Move.from_uci("e4d5"), "player")
    assert kinds(events) == [K.MOVE, K.CAPTURE]
    assert events[1].captured == chess.PAWN


def test_en_passant_captures_a_pawn():
    events = play("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "e5d6")
    assert kinds(events) == [K.MOVE, K.CAPTURE]
    assert events[1].captured == chess.PAWN


def test_castling():
    events = play("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1g1")
    assert kinds(events) == [K.MOVE, K.CASTLE]


def test_promotion():
    events = play("8/P6k/8/8/8/8/8/K7 w - - 0 1", "a7a8q")
    assert kinds(events) == [K.MOVE, K.PROMOTION]


def test_check_is_not_mate():
    events = play("4k3/8/8/8/8/8/8/4K2R w - - 0 1", "h1h8")
    assert kinds(events) == [K.MOVE, K.CHECK]


def test_checkmate_replaces_check_and_names_winner():
    board = chess.Board()
    for san in ("f3", "e5", "g4"):
        board.push_san(san)
    events = events_for_move(board, chess.Move.from_uci("d8h4"), "stockfih")
    assert kinds(events) == [K.MOVE, K.CHECKMATE]
    assert events[-1].winner == chess.BLACK


def test_stalemate():
    events = play("7k/5K2/8/6Q1/8/8/8/8 w - - 0 1", "g5g6")
    assert kinds(events) == [K.MOVE, K.STALEMATE]


def test_insufficient_material_draw_after_capture():
    events = play("4k3/8/8/8/8/8/3r4/3K4 w - - 0 1", "d1d2")
    assert kinds(events) == [K.MOVE, K.CAPTURE, K.DRAW]
    assert events[-1].reason == "insufficient_material"


def test_threefold_repetition_draw():
    board = chess.Board()
    for san in ("Nf3", "Nf6", "Ng1", "Ng8", "Nf3", "Nf6", "Ng1"):
        board.push_san(san)
    events = events_for_move(board, chess.Move.from_uci("f6g8"), "player")
    assert kinds(events)[-1] == K.DRAW
    assert events[-1].reason == "threefold_repetition"


def test_illegal_move_raises():
    with pytest.raises(ValueError):
        events_for_move(chess.Board(), chess.Move.from_uci("e2e5"), "player")


def test_unknown_mover_raises():
    with pytest.raises(ValueError):
        events_for_move(chess.Board(), chess.Move.from_uci("e2e4"), "nobody")


def test_board_is_not_changed():
    board = chess.Board()
    events_for_move(board, chess.Move.from_uci("e2e4"), "player")
    assert board.fen() == chess.STARTING_FEN and not board.move_stack
