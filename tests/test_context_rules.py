import re

import chess
import pytest

from stockfih.personality.commentary import Commentator, load_dialogue
from stockfih.personality.ego import Mood
from stockfih.personality.elo_personality import Tier
from stockfih.personality.events import EventKind as K
from stockfih.personality.events import GameEvent
from stockfih.personality.game_events import FactEvent
from stockfih.personality.game_phase import (
    ENDGAME_MAX_MATERIAL,
    Phase,
    game_phase,
    non_pawn_material,
)


class _First:
    # Stand-in rng: always the first usable line, so the test is repeatable.
    def choice(self, seq):
        return seq[0]


# --- game phase ---


def test_starting_position_is_sixty_two_points_and_an_opening():
    board = chess.Board()
    assert non_pawn_material(board) == 62
    assert game_phase(board) is Phase.OPENING


def test_many_pieces_after_move_ten_is_a_middlegame():
    board = chess.Board("r2q1rk1/ppp2ppp/2n1bn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 15")
    assert game_phase(board) is Phase.MIDDLEGAME


def test_move_ten_is_still_the_opening_and_eleven_is_not():
    fen = "r2q1rk1/ppp2ppp/2n1bn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 {}"
    assert game_phase(chess.Board(fen.format(10))) is Phase.OPENING
    assert game_phase(chess.Board(fen.format(11))) is Phase.MIDDLEGAME


def test_little_material_is_an_endgame_even_at_move_one():
    assert game_phase(chess.Board("4k3/8/8/3q4/8/2N5/8/4K3 w - - 0 1")) is Phase.ENDGAME


def test_endgame_boundary():
    at_limit = chess.Board("r3k3/8/8/8/8/8/8/RQ2K2R w - - 0 20")  # 9 + 5 + 5 + 5 = 24
    over = chess.Board("rn2k3/8/8/8/8/8/8/RQ2K2R w - - 0 20")  # one knight more = 27
    assert non_pawn_material(at_limit) == ENDGAME_MAX_MATERIAL
    assert game_phase(at_limit) is Phase.ENDGAME
    assert game_phase(over) is Phase.MIDDLEGAME


def test_pawns_and_kings_are_not_counted():
    assert non_pawn_material(chess.Board("4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")) == 0


# --- opening comments only while the game is in the opening ---

OPENING_DIALOGUE = {"toxic_comedian": {"game": {"opening": ["{text}? ok"]}}}


def opening_line(phase):
    c = Commentator("toxic_comedian", OPENING_DIALOGUE, _First())
    c.set_context(phase=phase)
    return c.comment([FactEvent(K.OPENING, "Sicilian")])


def test_opening_comment_is_allowed_in_the_opening_and_when_the_phase_is_unknown():
    assert opening_line(Phase.OPENING) == "Sicilian? ok"
    assert opening_line(None) == "Sicilian? ok"


@pytest.mark.parametrize("phase", [Phase.MIDDLEGAME, Phase.ENDGAME])
def test_opening_comment_is_blocked_later_in_the_game(phase):
    assert opening_line(phase) is None


def test_other_events_ignore_the_phase():
    dialogue = {"toxic_comedian": {"stockfih": {"capture": ["took it"]}}}
    event = [GameEvent(K.CAPTURE, "stockfih", 1, "Nxd5", chess.WHITE, captured=chess.PAWN)]
    for phase in (None, *Phase):
        c = Commentator("toxic_comedian", dialogue, _First())
        c.set_context(phase=phase)
        assert c.comment(event) == "took it"


def test_phase_must_be_a_phase_or_none():
    c = Commentator("toxic_comedian", OPENING_DIALOGUE, _First())
    with pytest.raises(ValueError):
        c.set_context(phase="opening")
    assert c.phase is None


# --- arrogant tiers stop gloating once the ego is not confident ---

TIER_DIALOGUE = {
    "toxic_comedian": {
        "stockfih": {"capture": ["base"]},
        "tiers": {
            "dominant": {"stockfih": {"capture": ["gloat"]}},
            "cocky": {"stockfih": {"capture": ["smug"]}},
            "rival": {"stockfih": {"capture": ["rival"]}},
        },
        "moods": {"excuses": {"stockfih": {"capture": ["excuse"]}}},
    }
}
CAP = [GameEvent(K.CAPTURE, "stockfih", 1, "Nxd5", chess.WHITE, captured=chess.PAWN)]


def line(tier, mood):
    c = Commentator("toxic_comedian", TIER_DIALOGUE, _First())
    c.set_context(tier=tier, mood=mood)
    return c.comment(CAP)


@pytest.mark.parametrize("mood", [None, Mood.CONFIDENT])
def test_dominant_and_cocky_gloat_while_confident_or_mood_unknown(mood):
    assert line(Tier.DOMINANT, mood) == "gloat"
    assert line(Tier.COCKY, mood) == "smug"


def test_dominant_stops_gloating_when_suspicious():
    assert line(Tier.DOMINANT, Mood.SUSPICIOUS) == "base"  # no suspicious line: plain fallback
    assert line(Tier.COCKY, Mood.SUSPICIOUS) == "base"


def test_the_mood_line_replaces_the_gloat_when_excusing():
    assert line(Tier.DOMINANT, Mood.EXCUSES) == "excuse"
    assert line(Tier.COCKY, Mood.EXCUSES) == "excuse"


@pytest.mark.parametrize("mood", [None, Mood.CONFIDENT, Mood.SUSPICIOUS])
def test_non_arrogant_tiers_keep_their_lines(mood):
    assert line(Tier.RIVAL, mood) == "rival"


def test_rival_tier_line_still_beats_the_mood_line():
    assert line(Tier.RIVAL, Mood.EXCUSES) == "rival"


# --- audit of the shipped lines ---

PHASE_WORDS = re.compile(r"\b(already|early|opening|middlegame|endgame)\b", re.IGNORECASE)


def kinds_and_lines(node):
    # (event kind, line) for every line; a list's key is the event kind.
    for key, value in node.items():
        if isinstance(value, list):
            for text in value:
                yield key, text
        else:
            yield from kinds_and_lines(value)


def test_only_opening_lines_talk_about_a_phase():
    for kind, text in kinds_and_lines(load_dialogue(profanity="spicy")):
        if kind != "opening":
            assert not PHASE_WORDS.search(text), f"{kind}: {text}"
