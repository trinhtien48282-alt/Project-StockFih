import random
import re

import chess
import pytest

from stockfih.personality.alien_language import (
    SYLLABLES,
    alien_for_events,
    alien_line,
    alien_mode_on,
    nonsense,
)
from stockfih.personality.cultural_rules import CulturalSettings
from stockfih.personality.events import EventKind as K
from stockfih.personality.events import GameEvent
from stockfih.personality.game_events import FactEvent


# --- nonsense ---


def test_nonsense_uses_only_the_syllable_list():
    rng = random.Random(1)
    for _ in range(200):
        for word in nonsense(rng, 1, 4).split():
            assert word in SYLLABLES


def test_word_count_stays_in_range():
    rng = random.Random(2)
    for _ in range(200):
        assert 1 <= len(nonsense(rng, 1, 3).split()) <= 3


def test_nonsense_contains_no_digits_so_no_binary():
    rng = random.Random(3)
    for _ in range(200):
        assert not re.search(r"\d", alien_line(rng))


def test_same_seed_gives_the_same_line():
    assert alien_line(random.Random(7), "e4") == alien_line(random.Random(7), "e4")


# --- move text ---


def test_the_move_is_the_only_real_token():
    rng = random.Random(4)
    for _ in range(100):
        line = alien_line(rng, "Qh5")
        words = re.findall(r"[A-Za-z0-9+#=]+", line)
        assert words.count("Qh5") == 1
        assert all(word == "Qh5" or word in SYLLABLES for word in words)


@pytest.mark.parametrize("bad", ["", "e 4", "x" * 13, "e4\n"])
def test_bad_move_text_is_refused(bad):
    with pytest.raises(ValueError):
        alien_line(random.Random(0), bad)


def test_alien_for_events_names_the_real_move():
    events = [GameEvent(K.CHECKMATE, "player", 9, "Qh5", chess.WHITE, winner=chess.WHITE)]
    assert "Qh5" in alien_for_events(events, random.Random(0))


def test_alien_for_events_needs_a_move():
    assert alien_for_events([], random.Random(0)) is None
    assert alien_for_events([FactEvent(K.MAJOR_SWING, "white")], random.Random(0)) is None


# --- gating ---


def test_alien_on_when_enabled_and_identity_unset():
    assert alien_mode_on(True, CulturalSettings())


def test_alien_on_when_identity_values_are_unknown():
    assert alien_mode_on(True, CulturalSettings(country="ZZ", origin="klingon"))


def test_alien_on_when_only_part_of_identity_is_set():
    assert alien_mode_on(True, CulturalSettings(country="VN"))
    assert alien_mode_on(True, CulturalSettings(origin="vietnamese"))


def test_alien_off_when_disabled():
    assert not alien_mode_on(False, CulturalSettings())


def test_alien_off_when_both_settings_are_configured():
    settings = CulturalSettings(enabled=True, country="VN", origin="vietnamese")
    assert not alien_mode_on(True, settings)
    # The identity opt-in itself does not matter for this check.
    assert not alien_mode_on(True, CulturalSettings(enabled=False, country="VN", origin="vietnamese"))
