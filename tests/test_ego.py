import chess
import pytest

from stockfih.personality.ego import CONFIDENT_MIN, MAX, MIN, START, SUSPICIOUS_MIN, Ego, Mood
from stockfih.personality.events import EventKind as K
from stockfih.personality.events import GameEvent
from stockfih.personality.game_events import FactEvent


def ev(kind, by="player"):
    return GameEvent(kind, by, 1, "e4", chess.WHITE)


def test_starts_confident_at_the_start_value():
    ego = Ego()
    assert ego.value == START
    assert ego.mood is Mood.CONFIDENT


@pytest.mark.parametrize("kind", [K.INACCURACY, K.MISTAKE, K.BLUNDER, K.MISSED_WIN])
def test_player_error_lifts_ego_and_own_error_lowers_it(kind):
    ego = Ego()
    ego.update(ev(kind, "player"))
    assert ego.value > START
    ego.reset()
    ego.update(ev(kind, "stockfih"))
    assert ego.value < START


def test_bigger_errors_move_the_ego_more():
    def drop(kind):
        ego = Ego()
        ego.update(ev(kind, "stockfih"))
        return START - ego.value

    assert drop(K.INACCURACY) < drop(K.MISTAKE) < drop(K.BLUNDER)


def test_ego_is_clamped():
    ego = Ego()
    for _ in range(50):
        ego.update(ev(K.BLUNDER, "player"))
    assert ego.value == MAX
    for _ in range(50):
        ego.update(ev(K.BLUNDER, "stockfih"))
    assert ego.value == MIN


def test_swing_toward_stockfih_lifts_ego_toward_player_lowers_it():
    ego = Ego(stockfih_color=chess.BLACK)
    ego.update(FactEvent(K.MAJOR_SWING, "black"))
    assert ego.value > START
    ego.reset()
    ego.update(FactEvent(K.MAJOR_SWING, "white"))
    assert ego.value < START


def test_swing_direction_follows_stockfihs_colour():
    ego = Ego(stockfih_color=chess.WHITE)
    ego.update(FactEvent(K.MAJOR_SWING, "white"))
    assert ego.value > START


def test_swing_with_unknown_side_is_ignored():
    ego = Ego()
    ego.update(FactEvent(K.MAJOR_SWING, ""))
    ego.update(FactEvent(K.MAJOR_SWING, "purple"))
    assert ego.value == START


@pytest.mark.parametrize("kind", [K.MOVE, K.CAPTURE, K.CHECK, K.CHECKMATE, K.CASTLE, K.PROMOTION])
def test_plain_events_do_not_move_the_ego(kind):
    ego = Ego()
    ego.update(ev(kind))
    assert ego.value == START


def test_game_facts_other_than_swings_are_ignored():
    ego = Ego()
    for kind in (K.GAME_WON, K.GAME_LOST, K.GAME_DRAWN, K.OPENING):
        ego.update(FactEvent(kind, "x"))
    assert ego.value == START


def test_mood_thresholds():
    ego = Ego()
    ego.value = CONFIDENT_MIN
    assert ego.mood is Mood.CONFIDENT
    ego.value = CONFIDENT_MIN - 1
    assert ego.mood is Mood.SUSPICIOUS
    ego.value = SUSPICIOUS_MIN
    assert ego.mood is Mood.SUSPICIOUS
    ego.value = SUSPICIOUS_MIN - 1
    assert ego.mood is Mood.EXCUSES


def test_ego_falls_through_the_moods_and_comes_back():
    ego = Ego()
    seen = []
    for _ in range(6):
        ego.update(ev(K.BLUNDER, "stockfih"))
        seen.append(ego.mood)
    assert seen[0] is Mood.SUSPICIOUS or seen[0] is Mood.CONFIDENT
    assert ego.mood is Mood.EXCUSES
    for _ in range(6):
        ego.update(ev(K.BLUNDER, "player"))
    assert ego.mood is Mood.CONFIDENT


def test_reset_restores_the_start_and_can_change_colour():
    ego = Ego()
    ego.update(ev(K.BLUNDER, "stockfih"))
    ego.reset(chess.WHITE)
    assert ego.value == START
    assert ego.stockfih_color == chess.WHITE
    ego.reset()
    assert ego.stockfih_color == chess.WHITE  # no colour given: unchanged


def test_mood_values_are_dialogue_keys():
    assert [m.value for m in Mood] == ["confident", "suspicious", "excuses"]
