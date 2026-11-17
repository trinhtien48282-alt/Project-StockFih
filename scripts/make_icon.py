# Renders the app SVG to build/stockfih.ico (the exe icon). Run from the project root.
# shortcut: one 256 px size in the .ico, Windows scales it down. Upgrade if small sizes look blurry.
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "src" / "stockfih" / "resources" / "images" / "stockfih.svg"
OUT = ROOT / "build" / "stockfih.ico"
SIZE = 256


def main() -> int:
    app = QGuiApplication([])  # Qt needs one alive to load its image plugins
    renderer = QSvgRenderer(str(SVG))
    if not renderer.isValid():
        print(f"Could not read {SVG}")
        return 1
    renderer.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)  # never stretch the fish
    image = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    OUT.parent.mkdir(exist_ok=True)
    if not image.save(str(OUT), "ICO"):
        print(f"Could not write {OUT}")
        return 1
    print(f"Wrote {OUT}")
    del app
    return 0


if __name__ == "__main__":
    sys.exit(main())
