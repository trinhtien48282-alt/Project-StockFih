import chess
from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from stockfih.chess.game import Game
from stockfih.ui.dialogs import ask_promotion

LIGHT = QColor("#f0d9b5")
DARK = QColor("#b58863")
LAST_MOVE = QColor(155, 199, 0, 105)
SELECTED = QColor(246, 246, 105, 150)
CHECK = QColor(220, 50, 50, 170)
TARGET = QColor(20, 85, 30, 120)


class BoardWidget(QWidget):
    def __init__(self, game: Game) -> None:
        super().__init__()
        self.game = game
        self.flipped = False
        self.selected: chess.Square | None = None
        self.targets: list[chess.Square] = []
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self) -> QSize:
        return QSize(640, 640)

    def flip(self) -> None:
        self.flipped = not self.flipped
        self.update()

    def _geometry(self) -> tuple[float, float, float]:
        side = min(self.width(), self.height()) / 8
        return side, (self.width() - 8 * side) / 2, (self.height() - 8 * side) / 2

    def _rect(self, sq: chess.Square) -> QRectF:
        side, ox, oy = self._geometry()
        file, rank = chess.square_file(sq), chess.square_rank(sq)
        col = 7 - file if self.flipped else file
        row = rank if self.flipped else 7 - rank
        return QRectF(ox + col * side, oy + row * side, side, side)

    def _square_at(self, pos: QPointF) -> chess.Square | None:
        side, ox, oy = self._geometry()
        col = int((pos.x() - ox) // side)
        row = int((pos.y() - oy) // side)
        if not (0 <= col < 8 and 0 <= row < 8):
            return None
        file = 7 - col if self.flipped else col
        rank = row if self.flipped else 7 - row
        return chess.square(file, rank)

    def _clear(self) -> None:
        self.selected = None
        self.targets = []

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        sq = self._square_at(event.position())
        if sq is None:
            return
        if self.selected is not None and sq in self.targets:
            promotion = None
            if self.game.needs_promotion(self.selected, sq):
                promotion = ask_promotion(self)
                if promotion is None:
                    return
            self.game.move(self.selected, sq, promotion)
            self._clear()
        else:
            piece = self.game.board.piece_at(sq)
            if piece and piece.color == self.game.board.turn:
                self.selected = sq
                self.targets = self.game.targets(sq)
            else:
                self._clear()
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        last = self.game.last_move
        check = self.game.check_square()
        for sq in chess.SQUARES:
            r = self._rect(sq)
            light = (chess.square_file(sq) + chess.square_rank(sq)) % 2 == 1
            p.fillRect(r, LIGHT if light else DARK)
            if last and sq in (last.from_square, last.to_square):
                p.fillRect(r, LAST_MOVE)
            if sq == self.selected:
                p.fillRect(r, SELECTED)
            if sq == check:
                p.fillRect(r, CHECK)
            piece = self.game.board.piece_at(sq)
            if piece:
                self._draw_piece(p, r, piece)
            if sq in self.targets:
                self._draw_target(p, r, occupied=piece is not None)

    def _draw_piece(self, p: QPainter, r: QRectF, piece: chess.Piece) -> None:
        font = QFont()
        font.setFamilies(["Segoe UI Symbol", "DejaVu Sans"])
        font.setPixelSize(int(r.width() * 0.8))
        path = QPainterPath()
        # Solid glyphs for both colors; fill color tells the sides apart.
        path.addText(0, 0, font, piece.unicode_symbol(invert_color=True))
        box = path.boundingRect()
        path.translate(r.center().x() - box.center().x(), r.center().y() - box.center().y())
        p.setPen(QPen(QColor("black"), max(1.0, r.width() * 0.03)))
        p.setBrush(QColor("white") if piece.color == chess.WHITE else QColor("#1a1a1a"))
        p.drawPath(path)

    def _draw_target(self, p: QPainter, r: QRectF, occupied: bool) -> None:
        c = r.center()
        if occupied:
            p.setPen(QPen(TARGET, r.width() * 0.08))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(c, r.width() * 0.42, r.width() * 0.42)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(TARGET)
            p.drawEllipse(c, r.width() * 0.15, r.width() * 0.15)