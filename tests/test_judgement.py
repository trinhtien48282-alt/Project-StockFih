import chess
import pytest

from stockfih.engine.stockfih import MATE, MATE_BOUND as ENGINE_MATE_BOUND
from stockfih.personality.events import EventKind as K
from stockfih.personality.judgement import MATE_BOUND, judge, judgement_event

M = MATE - 3  # a score meaning "I mate in 3 plies"


def test_mate_bound_matches_the_engine():
    assert MATE_BOUND == ENGINE_MATE_BOUND


@pytest.mark.parametrize(
    "best, played, expected",
    [
        # plain centipawn loss, on the edges of each threshold
        (0, 0, None),
        (0, -49, None),
        (0, -50, K.INACCURACY),
        (0, -99, K.INACCURACY),
        (0, -100, K.MISTAKE),
        (0, -199, K.MISTAKE),
        (0, -200, K.BLUNDER),
        (0, -900, K.BLUNDER),
        # depth noise: a move scoring better than the "best" is not a loss
        (0, 100, None),
        # nobody to blame when the same side is decisively ahead before and after
        (900, 700, None),
        (-800, -1000, None),
        # a win thrown away, but not yet lost
        (500, 0, K.MISSED_WIN),
        (350, 200, K.MISSED_WIN),
        (350, 280, K.INACCURACY),
        (300, 299, None),
        # a win turned into a loss is a blunder
        (500, -400, K.BLUNDER),
        # mates
        (M, 100, K.MISSED_WIN),
        (M, MATE - 5, None),
        (0, -M, K.BLUNDER),
        (-100, -M, K.BLUNDER),
        (-500, -M, None),
        (-M, -(MATE - 5), None),
    ],
)
def test_judge(best, played, expected):
    assert judge(best, played) == expected


def test_event_for_a_blunder():
    board = chess.Board()
    event = judgement_event(board, chess.Move.from_uci("e2e4"), "player", 0, -250)
    assert event.kind == K.BLUNDER
    assert event.loss == 250
    assert (event.san, event.ply, event.color, event.by) == ("e4", 1, chess.WHITE, "player")


def test_event_loss_is_none_for_mate_scores():
    event = judgement_event(chess.Board(), chess.Move.from_uci("e2e4"), "stockfih", M, 0)
    assert event.kind == K.MISSED_WIN
    assert event.loss is None


def test_no_event_for_a_fine_move():
    assert judgement_event(chess.Board(), chess.Move.from_uci("e2e4"), "player", 0, -10) is None


def test_illegal_move_raises():
    with pytest.raises(ValueError):
        judgement_event(chess.Board(), chess.Move.from_uci("e2e5"), "player", 0, 0)


def test_unknown_mover_raises():
    with pytest.raises(ValueError):
        judgement_event(chess.Board(), chess.Move.from_uci("e2e4"), "nobody", 0, 0)


def test_board_is_not_changed():
    board = chess.Board()
    judgement_event(board, chess.Move.from_uci("e2e4"), "player", 0, -250)
    assert board.fen() == chess.STARTING_FEN and not board.move_stack
