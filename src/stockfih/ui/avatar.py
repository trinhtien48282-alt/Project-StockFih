from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

SIZE = 96


def save_avatar(source: Path, dest: Path) -> None:
    # Center-crops to a square, shrinks to SIZE, stores as PNG. Raises ValueError on a bad image.
    image = QImage(str(source))
    if image.isNull():
        raise ValueError("Could not read that image.")
    side = min(image.width(), image.height())
    square = image.copy((image.width() - side) // 2, (image.height() - side) // 2, side, side)
    square = square.scaled(
        SIZE, SIZE, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not square.save(str(dest), "PNG"):
        raise ValueError("Could not save the avatar.")


def load_avatar(path: Path) -> QPixmap | None:
    pixmap = QPixmap(str(path))
    return None if pixmap.isNull() else pixmap
