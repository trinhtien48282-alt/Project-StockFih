from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QSoundEffect

_DIR = Path(__file__).resolve().parent.parent / "resources" / "sounds"


class Sounds:
    def __init__(self, parent: QObject) -> None:
        self.enabled = True
        self._effects: dict[str, QSoundEffect] = {}
        for name in ("move", "capture", "end"):
            path = _DIR / f"{name}.wav"
            if path.is_file():
                effect = QSoundEffect(parent)
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(0.6)
                self._effects[name] = effect

    def play(self, name: str) -> None:
        effect = self._effects.get(name)
        if self.enabled and effect is not None:
            effect.play()
