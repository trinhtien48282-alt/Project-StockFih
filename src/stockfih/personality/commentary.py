import json
import random
import string
from pathlib import Path

import chess

from stockfih.personality.ego import Mood
from stockfih.personality.elo_personality import Tier
from stockfih.personality.events import EventKind, GameEvent
from stockfih.personality.game_events import FactEvent

# Turns structured events into one line of text. It only decides what to SAY: it imports no
# engine and no GUI, and nothing here can change a move. A line is only ever chosen for an
# event that really happened, and a line that needs a value the event does not have is skipped.
# Commentary text lives in resources/ (that folder is what the Windows build ships).
# Text taken from a PGN header (the opening name) is external data: show it as plain text.
#
# Context lines (Phase 10.3): a line under "tiers" or "moods" is used only when set_context()
# names that tier or ego mood. The plain line is the fallback. The tier and mood lines are in
# resources/dialogue_context.json and are merged in by load_dialogue().

MODES = ("toxic_comedian", "professional", "silent")
SPEAKERS = ("player", "stockfih", "game")  # who moved; "game" = facts about the whole game
FIELDS = {"san", "ply", "captured", "winner", "reason", "loss", "text"}
DIALOGUE_PATH = Path(__file__).resolve().parent.parent / "resources" / "dialogue.json"
CONTEXT_PATH = Path(__file__).resolve().parent.parent / "resources" / "dialogue_context.json"
CONTEXT_VALUES = {
    "tiers": frozenset(tier.value for tier in Tier),
    "moods": frozenset(mood.value for mood in Mood),
}

# When one move carries several events, the first kind in this list that has a usable line wins.
# MOVE is last and has no lines on purpose: a plain move gets no comment.
PRIORITY = (
    EventKind.CHECKMATE,
    EventKind.STALEMATE,
    EventKind.DRAW,
    EventKind.GAME_WON,
    EventKind.GAME_LOST,
    EventKind.GAME_DRAWN,
    EventKind.BLUNDER,
    EventKind.MISSED_WIN,
    EventKind.MISTAKE,
    EventKind.INACCURACY,
    EventKind.MAJOR_SWING,
    EventKind.PROMOTION,
    EventKind.CHECK,
    EventKind.CAPTURE,
    EventKind.CASTLE,
    EventKind.OPENING,
    EventKind.MOVE,
)


def _fields(line: str) -> set[str]:
    # Names used in a line like "{san} takes {captured}". ValueError for a bad template.
    names = set()
    for _literal, name, spec, conversion in string.Formatter().parse(line):
        if name is None:
            continue
        if spec or conversion:
            raise ValueError(f"Unsupported format in line: {line!r}")
        names.add(name)
    return names


def _check_by_kind(where: str, by_kind: object, kinds: set[str]) -> None:
    # {event kind: [lines]} for one speaker.
    if not isinstance(by_kind, dict):
        raise ValueError(f"{where} must be an object.")
    for kind, lines in by_kind.items():
        here = f"{where}/{kind}"
        if kind not in kinds:
            raise ValueError(f"Unknown event kind in {where}: {kind!r}.")
        if not isinstance(lines, list) or not lines:
            raise ValueError(f"{here} needs a non-empty list of lines.")
        for line in lines:
            if not isinstance(line, str) or not line.strip():
                raise ValueError(f"{here} has a line that is not text.")
            unknown = _fields(line) - FIELDS
            if unknown:
                raise ValueError(f"{here} uses unknown field(s) {sorted(unknown)}: {line!r}")


def check_dialogue(data: object) -> None:
    # Raises ValueError naming the first problem.
    # Shape: {mode: {speaker: {kind: [lines]}, "tiers": {tier: {speaker: {...}}}, "moods": {...}}}.
    kinds = {kind.value for kind in EventKind}
    if not isinstance(data, dict):
        raise ValueError("Dialogue must be a JSON object.")
    for mode, body in data.items():
        if mode not in MODES or mode == "silent":
            raise ValueError(f"Unknown commentary mode: {mode!r}")
        if not isinstance(body, dict):
            raise ValueError(f"Mode {mode!r} must be an object.")
        for name, section in body.items():
            if name in SPEAKERS:
                _check_by_kind(f"{mode}/{name}", section, kinds)
            elif name in CONTEXT_VALUES:
                where = f"{mode}/{name}"
                if not isinstance(section, dict):
                    raise ValueError(f"{where} must be an object.")
                for value, speakers in section.items():
                    if value not in CONTEXT_VALUES[name]:
                        raise ValueError(f"Unknown {name[:-1]} {value!r} in {where}.")
                    if not isinstance(speakers, dict):
                        raise ValueError(f"{where}/{value} must be an object.")
                    for speaker, by_kind in speakers.items():
                        if speaker not in SPEAKERS:
                            raise ValueError(f"Unknown speaker {speaker!r} in {where}/{value}.")
                        _check_by_kind(f"{where}/{value}/{speaker}", by_kind, kinds)
            else:
                raise ValueError(f"Unknown section {name!r} in {mode!r}.")


def _read(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Could not read the dialogue file: {error}") from None


def load_dialogue(path: Path | None = None) -> dict:
    # With no path: the shipped dialogue, with the shipped tier and mood lines merged in.
    # With a path: that one file only. ValueError if a file is unreadable or invalid.
    if path is not None:
        data = _read(path)
        check_dialogue(data)
        return data
    data = _read(DIALOGUE_PATH)
    check_dialogue(data)
    context = _read(CONTEXT_PATH)
    check_dialogue(context)
    for mode, body in context.items():
        target = data.setdefault(mode, {})
        for name, section in body.items():
            bucket = target.setdefault(name, {})
            for key, value in section.items():
                bucket.setdefault(key, {}).update(value)
    check_dialogue(data)
    return data


def _values(event: GameEvent | FactEvent) -> dict[str, object]:
    # Only values the event really has. A missing value is left out, never filled in.
    values: dict[str, object] = {}
    if isinstance(event, GameEvent):
        values["san"] = event.san
        values["ply"] = event.ply
        if event.captured is not None:
            values["captured"] = chess.piece_name(event.captured)
        if event.winner is not None:
            values["winner"] = "White" if event.winner == chess.WHITE else "Black"
        if event.reason:
            values["reason"] = event.reason.replace("_", " ")
        if event.loss is not None:
            values["loss"] = event.loss
    elif event.text:
        values["text"] = event.text
    return values


class Commentator:
    def __init__(
        self,
        mode: str = "professional",
        dialogue: dict | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.set_mode(mode)
        if dialogue is not None:
            check_dialogue(dialogue)
        self.dialogue = dialogue if dialogue is not None else load_dialogue()
        self._rng = rng or random.Random()
        self.tier: Tier | None = None
        self.mood: Mood | None = None

    def set_mode(self, mode: str) -> None:
        # ValueError for an unknown mode; the old mode stays.
        if mode not in MODES:
            raise ValueError(f"Mode must be one of {MODES}.")
        self.mode = mode

    def set_context(self, tier: Tier | None = None, mood: Mood | None = None) -> None:
        # The rating tier and the ego mood for the lines that follow. None means neutral.
        # ValueError if a value is not a Tier or a Mood; the old context stays.
        if tier is not None and not isinstance(tier, Tier):
            raise ValueError("tier must be a Tier or None.")
        if mood is not None and not isinstance(mood, Mood):
            raise ValueError("mood must be a Mood or None.")
        self.tier, self.mood = tier, mood

    def _pools(self, speaker: str, kind: str) -> list[list[str]]:
        # Most specific first: tier line, then mood line, then the plain line.
        # Professional has no context lines, so it always gets the plain line.
        modes = self.dialogue.get(self.mode, {})
        pools = []
        if self.tier is not None:
            tier_lines = modes.get("tiers", {}).get(self.tier.value, {})
            pools.append(tier_lines.get(speaker, {}).get(kind, []))
        if self.mood is not None:
            mood_lines = modes.get("moods", {}).get(self.mood.value, {})
            pools.append(mood_lines.get(speaker, {}).get(kind, []))
        pools.append(modes.get(speaker, {}).get(kind, []))
        return pools

    def _line(
        self, event: GameEvent | FactEvent, avoid: frozenset[str] | set[str] = frozenset()
    ) -> str | None:
        speaker = event.by if isinstance(event, GameEvent) else "game"
        values = _values(event)
        for lines in self._pools(speaker, event.kind.value):
            usable = [line for line in lines if _fields(line) <= values.keys()]
            if not usable:
                continue
            texts = [line.format(**values) for line in usable]
            fresh = [text for text in texts if text not in avoid]
            return self._rng.choice(fresh or texts)
        return None

    def comment(
        self,
        events: list[GameEvent | FactEvent],
        avoid: frozenset[str] | set[str] = frozenset(),
    ) -> str | None:
        # One line for the most notable event, or None. `avoid` holds recently said lines:
        # one of them is used only when no other line fits.
        if self.mode == "silent":
            return None
        for kind in PRIORITY:
            for event in events:
                if event.kind == kind:
                    line = self._line(event, avoid)
                    if line:
                        return line
        return None
