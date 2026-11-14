from dataclasses import dataclass

from PySide6.QtGui import QColor


@dataclass(frozen=True)
class SquareTheme:
    light: QColor
    dark: QColor


@dataclass(frozen=True)
class PieceTheme:
    white: QColor
    black: QColor
    outline: QColor


# The first entry of each dict is the default.
SQUARE_THEMES = {
    "Brown": SquareTheme(QColor("#f0d9b5"), QColor("#b58863")),
    "Green": SquareTheme(QColor("#eeeed2"), QColor("#769656")),
    "Blue": SquareTheme(QColor("#dee3e6"), QColor("#8ca2ad")),
    "Gray": SquareTheme(QColor("#d9d9d9"), QColor("#8a8a8a")),
}

PIECE_THEMES = {
    "Classic": PieceTheme(QColor("white"), QColor("#1a1a1a"), QColor("black")),
    "Ivory & Ebony": PieceTheme(QColor("#fffff0"), QColor("#2b1d14"), QColor("#3b2a1e")),
    "Red & Blue": PieceTheme(QColor("#ff6b6b"), QColor("#3b5bdb"), QColor("black")),
}
