import random

import chess
import pytest

from stockfih.personality.commentary import Commentator, check_dialogue, load_dialogue
from stockfih.personality.ego import Mood
from stockfih.personality.elo_personality import Tier
from stockfih.personality.events import EventKind as K
from stockfih.personality.events import GameEvent


class _First:
    # Stand-in rng: always the first usable line, so the test is repeatable.
    def choice(self, seq):
        return seq[0]


def cap():
    return [GameEvent(K.CAPTURE, "stockfih", 1, "Nxd5", chess.WHITE, captured=chess.PAWN)]


DIALOG = {
    "toxic_comedian": {
        "stockfih": {"capture": ["base {captured}"]},
        "tiers": {"dominant": {"stockfih": {"capture": ["tier {captured}"]}}},
        "moods": {"excuses": {"stockfih": {"capture": ["mood {captured}"]}}},
    }
}


def make() -> Commentator:
    return Commentator("toxic_comedian", DIALOG, _First())


# --- selection ---


def test_without_context_the_plain_line_is_used():
    assert make().comment(cap()) == "base pawn"


def test_tier_line_is_used_when_the_tier_is_set():
    c = make()
    c.set_context(tier=Tier.DOMINANT)
    assert c.comment(cap()) == "tier pawn"


def test_tier_without_a_matching_line_falls_back_to_plain():
    c = make()
    c.set_context(tier=Tier.RIVAL)
    assert c.comment(cap()) == "base pawn"


def test_mood_line_is_used_when_no_tier_is_set():
    c = make()
    c.set_context(mood=Mood.EXCUSES)
    assert c.comment(cap()) == "mood pawn"


def test_tier_line_beats_mood_line():
    c = make()
    c.set_context(tier=Tier.DOMINANT, mood=Mood.EXCUSES)
    assert c.comment(cap()) == "tier pawn"


def test_mood_line_used_when_the_tier_has_none():
    c = make()
    c.set_context(tier=Tier.RIVAL, mood=Mood.EXCUSES)
    assert c.comment(cap()) == "mood pawn"


def test_clearing_the_context_returns_to_plain_lines():
    c = make()
    c.set_context(tier=Tier.DOMINANT)
    c.set_context()
    assert c.comment(cap()) == "base pawn"


def test_context_must_be_a_tier_or_mood():
    c = make()
    with pytest.raises(ValueError):
        c.set_context(tier="dominant")
    with pytest.raises(ValueError):
        c.set_context(mood="excuses")
    assert c.tier is None and c.mood is None


def test_professional_mode_ignores_context():
    plain = Commentator("professional", rng=_First())
    tiered = Commentator("professional", rng=_First())
    tiered.set_context(tier=Tier.DOMINANT, mood=Mood.EXCUSES)
    assert plain.comment(cap()) == tiered.comment(cap())


# --- shipped file ---


def test_shipped_context_covers_every_tier_and_mood():
    toxic = load_dialogue()["toxic_comedian"]
    assert set(toxic["tiers"]) == {tier.value for tier in Tier}
    assert set(toxic["moods"]) == {mood.value for mood in Mood}
    for tier in Tier:
        assert toxic["tiers"][tier.value]["stockfih"], tier


def test_shipped_professional_has_no_context_lines():
    professional = load_dialogue()["professional"]
    assert "tiers" not in professional
    assert "moods" not in professional


def test_shipped_tier_line_is_used_in_game():
    c = Commentator("toxic_comedian", rng=random.Random(0))
    c.set_context(tier=Tier.EXISTENTIAL_CRISIS)
    line = c.comment(
        [GameEvent(K.BLUNDER, "stockfih", 4, "Qh5", chess.BLACK, loss=150)]
    )
    assert line in {
        "Qh5?! MY CREATOR DID NOT PREPARE ME FOR THIS.",
    }


# --- checks ---


@pytest.mark.parametrize(
    "bad",
    [
        {"toxic_comedian": {"tiers": {"godlike": {"stockfih": {"capture": ["x"]}}}}},
        {"toxic_comedian": {"moods": {"angry": {"stockfih": {"capture": ["x"]}}}}},
        {"toxic_comedian": {"tiers": {"rival": {"nobody": {"capture": ["x"]}}}}},
        {"toxic_comedian": {"tiers": {"rival": {"stockfih": {"nope": ["x"]}}}}},
        {"toxic_comedian": {"tiers": {"rival": {"stockfih": {"capture": ["{nope}"]}}}}},
        {"toxic_comedian": {"tiers": ["rival"]}},
        {"toxic_comedian": {"tiers": {"rival": ["x"]}}},
        {"toxic_comedian": {"tiers": {"rival": {"stockfih": ["x"]}}}},
    ],
)
def test_bad_context_is_rejected(bad):
    with pytest.raises(ValueError):
        check_dialogue(bad)


def test_valid_context_section_is_accepted():
    check_dialogue(DIALOG)
