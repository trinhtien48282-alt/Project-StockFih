import chess
from PySide6.QtCore import QEasingCurve, QPointF, QRectF, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from stockfih.chess.game import Game
from stockfih.ui.dialogs import ask_promotion
from stockfih.ui.themes import PIECE_THEMES, SQUARE_THEMES, PieceTheme, SquareTheme

LAST_MOVE = QColor(155, 199, 0, 105)
SELECTED = QColor(246, 246, 105, 150)
CHECK = QColor(220, 50, 50, 170)
TARGET = QColor(20, 85, 30, 120)
SLIDE_MS = 160


class BoardWidget(QWidget):
    changed = Signal()  # emitted whenever the game state changes
    moved = Signal()  # emitted after the player makes a move on the board

    def __init__(self, game: Game) -> None:
        super().__init__()
        self.game = game
        self.flipped = False
        self.animate = True
        self.selected: chess.Square | None = None
        self.targets: list[chess.Square] = []
        self.square_theme = next(iter(SQUARE_THEMES.values()))
        self.piece_theme = next(iter(PIECE_THEMES.values()))
        self._anim: QVariantAnimation | None = None
        self._moving: tuple[chess.Square, chess.Square, chess.Piece] | None = None
        self._progress = 0.0
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self) -> QSize:
        return QSize(640, 640)

    def set_themes(self, squares: SquareTheme, pieces: PieceTheme) -> None:
        self.square_theme = squares
        self.piece_theme = pieces
        self.update()

    def flip(self) -> None:
        self.flipped = not self.flipped
        self.update()

    def refresh(self, animate: bool = False) -> None:
        # Call after changing the game from outside (undo, redo, new game, restart).
        # animate=True slides the piece of the latest move (use it for forward steps only).
        self._clear()
        if animate:
            self._animate_last()
        else:
            self._stop_anim()
        self.update()
        self.changed.emit()

    def _animate_last(self) -> None:
        self._stop_anim()
        move = self.game.last_move
        piece = self.game.board.piece_at(move.to_square) if move else None
        if not self.animate or piece is None:
            return
        self._moving = (move.from_square, move.to_square, piece)
        self._progress = 0.0
        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(SLIDE_MS)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.valueChanged.connect(self._on_progress)
        anim.finished.connect(self._finish_anim)
        self._anim = anim
        anim.start()

    def _on_progress(self, value) -> None:
        self._progress = float(value)
        self.update()

    def _finish_anim(self) -> None:
        self._stop_anim()
        self.update()

    def _stop_anim(self) -> None:
        if self._anim is not None:
            self._anim.stop()
            self._anim.deleteLater()
            self._anim = None
        self._moving = None

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
            self._animate_last()
            self.changed.emit()
            self.moved.emit()
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
        moving = self._moving
        for sq in chess.SQUARES:
            r = self._rect(sq)
            light = (chess.square_file(sq) + chess.square_rank(sq)) % 2 == 1
            p.fillRect(r, self.square_theme.light if light else self.square_theme.dark)
            if last and sq in (last.from_square, last.to_square):
                p.fillRect(r, LAST_MOVE)
            if sq == self.selected:
                p.fillRect(r, SELECTED)
            if sq == check:
                p.fillRect(r, CHECK)
            piece = self.game.board.piece_at(sq)
            if piece and not (moving and sq == moving[1]):
                self._draw_piece(p, r, piece)
            if sq in self.targets:
                self._draw_target(p, r, occupied=piece is not None)
        if moving:
            start, end, piece = moving
            a, b, t = self._rect(start), self._rect(end), self._progress
            slide = QRectF(
                a.x() + (b.x() - a.x()) * t, a.y() + (b.y() - a.y()) * t, a.width(), a.height()
            )
            self._draw_piece(p, slide, piece)

    def _draw_piece(self, p: QPainter, r: QRectF, piece: chess.Piece) -> None:
        font = QFont()
        font.setFamilies(["Segoe UI Symbol", "DejaVu Sans"])
        font.setPixelSize(int(r.width() * 0.8))
        path = QPainterPath()
        # Solid glyphs for both colors; fill color tells the sides apart.
        path.addText(0, 0, font, piece.unicode_symbol(invert_color=True))
        box = path.boundingRect()
        path.translate(r.center().x() - box.center().x(), r.center().y() - box.center().y())
        theme = self.piece_theme
        p.setPen(QPen(theme.outline, max(1.0, r.width() * 0.03)))
        p.setBrush(theme.white if piece.color == chess.WHITE else theme.black)
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
