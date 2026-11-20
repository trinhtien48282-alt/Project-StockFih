import json
import random
import string
from pathlib import Path

import chess

from stockfih.personality.events import EventKind, GameEvent
from stockfih.personality.game_events import FactEvent

# Turns structured events into one line of text. It only decides what to SAY: it imports no
# engine and no GUI, and nothing here can change a move. A line is only ever chosen for an
# event that really happened, and a line that needs a value the event does not have is skipped.
# Commentary text lives in resources/dialogue.json (that folder is what the Windows build ships).
# Text taken from a PGN header (the opening name) is external data: show it as plain text.

MODES = ("toxic_comedian", "professional", "silent")
SPEAKERS = ("player", "stockfih", "game")  # who moved; "game" = facts about the whole game
FIELDS = {"san", "ply", "captured", "winner", "reason", "loss", "text"}
DIALOGUE_PATH = Path(__file__).resolve().parent.parent / "resources" / "dialogue.json"

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


def check_dialogue(data: object) -> None:
    # Raises ValueError naming the first problem. Shape: {mode: {speaker: {event kind: [lines]}}}.
    kinds = {kind.value for kind in EventKind}
    if not isinstance(data, dict):
        raise ValueError("Dialogue must be a JSON object.")
    for mode, speakers in data.items():
        if mode not in MODES or mode == "silent":
            raise ValueError(f"Unknown commentary mode: {mode!r}")
        if not isinstance(speakers, dict):
            raise ValueError(f"Mode {mode!r} must be an object.")
        for speaker, by_kind in speakers.items():
            if speaker not in SPEAKERS:
                raise ValueError(f"Unknown speaker {speaker!r} in {mode!r}.")
            if not isinstance(by_kind, dict):
                raise ValueError(f"{mode}/{speaker} must be an object.")
            for kind, lines in by_kind.items():
                where = f"{mode}/{speaker}/{kind}"
                if kind not in kinds:
                    raise ValueError(f"Unknown event kind in {where}.")
                if not isinstance(lines, list) or not lines:
                    raise ValueError(f"{where} needs a non-empty list of lines.")
                for line in lines:
                    if not isinstance(line, str) or not line.strip():
                        raise ValueError(f"{where} has a line that is not text.")
                    unknown = _fields(line) - FIELDS
                    if unknown:
                        raise ValueError(f"{where} uses unknown field(s) {sorted(unknown)}: {line!r}")


def load_dialogue(path: Path | None = None) -> dict:
    # Reads and checks the dialogue file. ValueError if it is unreadable or invalid.
    try:
        data = json.loads((path or DIALOGUE_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Could not read the dialogue file: {error}") from None
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

    def set_mode(self, mode: str) -> None:
        # ValueError for an unknown mode; the old mode stays.
        if mode not in MODES:
            raise ValueError(f"Mode must be one of {MODES}.")
        self.mode = mode

    def _line(self, event: GameEvent | FactEvent) -> str | None:
        speaker = event.by if isinstance(event, GameEvent) else "game"
        lines = self.dialogue.get(self.mode, {}).get(speaker, {}).get(event.kind.value, [])
        values = _values(event)
        usable = [line for line in lines if _fields(line) <= values.keys()]
        return self._rng.choice(usable).format(**values) if usable else None

    def comment(self, events: list[GameEvent | FactEvent]) -> str | None:
        # One line for the most notable event, or None (silent mode, or nothing worth saying).
        if self.mode == "silent":
            return None
        for kind in PRIORITY:
            for event in events:
                if event.kind == kind:
                    line = self._line(event)
                    if line:
                        return line
        return None
