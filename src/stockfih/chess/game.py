import chess


class Game:
    def __init__(self) -> None:
        self.board = chess.Board()

    def outcome(self) -> chess.Outcome | None:
        # Mate, stalemate, insufficient material, 75-move, fivefold: python-chess ends these itself.
        # Threefold and 50-move are claims in real chess. We apply them automatically, but
        # only once the position has actually occurred / the clock has actually reached it.
        out = self.board.outcome()
        if out is not None:
            return out
        if self.board.is_repetition(3):
            return chess.Outcome(chess.Termination.THREEFOLD_REPETITION, None)
        if self.board.is_fifty_moves():
            return chess.Outcome(chess.Termination.FIFTY_MOVES, None)
        return None

    def targets(self, square: chess.Square) -> list[chess.Square]:
        if self.outcome() is not None:
            return []
        return [m.to_square for m in self.board.legal_moves if m.from_square == square]

    def needs_promotion(self, from_sq: chess.Square, to_sq: chess.Square) -> bool:
        piece = self.board.piece_at(from_sq)
        return bool(piece and piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in (0, 7))

    def move(
        self,
        from_sq: chess.Square,
        to_sq: chess.Square,
        promotion: chess.PieceType | None = None,
    ) -> bool:
        move = chess.Move(from_sq, to_sq, promotion=promotion)
        if self.outcome() is not None or move not in self.board.legal_moves:
            return False
        self.board.push(move)
        return True

    @property
    def last_move(self) -> chess.Move | None:
        return self.board.move_stack[-1] if self.board.move_stack else None

    def check_square(self) -> chess.Square | None:
        return self.board.king(self.board.turn) if self.board.is_check() else None