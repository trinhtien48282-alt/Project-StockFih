import json
import random
import re

import pytest

from stockfih.personality.commentary import (
    CONTEXT_PATH,
    DIALOGUE_PATH,
    IDENTITY_PATH,
    MILD_PATH,
    PROFANITY_LEVELS,
    SPICY_PATH,
    Commentator,
    check_dialogue,
    load_dialogue,
)
from stockfih.personality.elo_personality import Tier
from stockfih.personality.events import EventKind as K
from stockfih.personality.game_events import FactEvent

MILD_WORDS = re.compile(r"\b(damn\w*|hell|crap)\b", re.IGNORECASE)
SPICY_WORDS = re.compile(r"\b(fuck\w*|shit\w*)", re.IGNORECASE)


def lines(node) -> list[str]:
    # Every line in a dialogue structure, whatever the nesting.
    if isinstance(node, list):
        return [x for x in node]
    return [x for child in node.values() for x in lines(child)]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def count(level: str) -> int:
    return len(lines(load_dialogue(profanity=level)))


def said(level: str, tier: Tier | None = None, seeds: int = 60) -> set[str]:
    out = set()
    for seed in range(seeds):
        c = Commentator("toxic_comedian", rng=random.Random(seed), profanity=level)
        c.set_context(tier=tier)
        out.add(c.comment([FactEvent(K.GAME_LOST)]))
    return out


# --- files ---


def test_levels_are_clean_mild_spicy():
    assert PROFANITY_LEVELS == ("clean", "mild", "spicy")


@pytest.mark.parametrize("path", [MILD_PATH, SPICY_PATH])
def test_extra_files_are_valid_and_toxic_only(path):
    data = read(path)
    check_dialogue(data)
    assert set(data) == {"toxic_comedian"}


def test_clean_lines_contain_no_profanity():
    for path in (DIALOGUE_PATH, CONTEXT_PATH, IDENTITY_PATH):
        for line in lines(read(path)):
            assert not MILD_WORDS.search(line) and not SPICY_WORDS.search(line), line


def test_mild_file_has_no_strong_words():
    assert not any(SPICY_WORDS.search(line) for line in lines(read(MILD_PATH)))


def test_spicy_file_has_the_roadmap_lines():
    text = " ".join(lines(read(SPICY_PATH)))
    assert "GG FUCKING EZZZ." in text
    assert "THIS IS FUCKING RIGGED." in text


# --- loading ---


def test_each_level_adds_lines():
    assert count("clean") < count("mild") < count("spicy")


def test_default_load_is_clean():
    assert load_dialogue() == load_dialogue(profanity="clean")


def test_professional_is_the_same_at_every_level():
    clean = load_dialogue(profanity="clean")["professional"]
    assert load_dialogue(profanity="mild")["professional"] == clean
    assert load_dialogue(profanity="spicy")["professional"] == clean


def test_unknown_level_is_refused():
    with pytest.raises(ValueError):
        load_dialogue(profanity="loud")
    with pytest.raises(ValueError):
        Commentator("toxic_comedian", profanity="loud")


# --- commentator ---


def test_roadmap_line_appears_only_at_spicy():
    line = "GG FUCKING EZZZ."
    assert line in said("spicy", Tier.DOMINANT)
    assert line not in said("mild", Tier.DOMINANT)
    assert line not in said("clean", Tier.DOMINANT)


def test_mild_word_lines_appear_at_mild_but_not_clean():
    assert any(MILD_WORDS.search(x) for x in said("mild"))
    assert not any(MILD_WORDS.search(x) for x in said("clean"))


def test_clean_commentator_says_nothing_profane():
    for x in said("clean") | said("clean", Tier.DOMINANT):
        assert not MILD_WORDS.search(x) and not SPICY_WORDS.search(x)


def test_set_profanity_changes_the_lines_and_keeps_old_ones_on_error():
    c = Commentator("toxic_comedian", rng=random.Random(1))
    before = c.dialogue
    c.set_profanity("spicy")
    assert c.profanity == "spicy" and c.dialogue != before
    with pytest.raises(ValueError):
        c.set_profanity("loud")
    assert c.profanity == "spicy"


def test_own_dialogue_has_no_levels():
    c = Commentator("toxic_comedian", {"toxic_comedian": {"game": {"game_lost": ["x"]}}})
    with pytest.raises(ValueError):
        c.set_profanity("spicy")
