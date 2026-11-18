import chess

DOUBLED_CP = 15  # per extra pawn on a file
ISOLATED_CP = 15  # per pawn with no friendly pawn on a neighboring file
# Passed-pawn bonus by rank counted from the pawn's own side: index 1 = 2nd rank, 6 = 7th rank.
PASSED_CP = (0, 5, 10, 20, 40, 70, 120, 0)
# All values are starting points to tune in Phase 14.


def _side(board: chess.Board, color: chess.Color) -> int:
    pawns = list(board.pieces(chess.PAWN, color))
    enemy = list(board.pieces(chess.PAWN, not color))
    per_file = [0] * 8
    for square in pawns:
        per_file[chess.square_file(square)] += 1

    score = 0
    for count in per_file:
        if count > 1:
            score -= DOUBLED_CP * (count - 1)
    for square in pawns:
        file, rank = chess.square_file(square), chess.square_rank(square)
        has_neighbor = (file > 0 and per_file[file - 1] > 0) or (file < 7 and per_file[file + 1] > 0)
        if not has_neighbor:
            score -= ISOLATED_CP
        # Passed: no enemy pawn in front of it on its own file or a neighboring one.
        # An enemy pawn on the same rank (beside it) does not block.
        blocked = any(
            abs(chess.square_file(e) - file) <= 1
            and (chess.square_rank(e) > rank if color == chess.WHITE else chess.square_rank(e) < rank)
            for e in enemy
        )
        if not blocked:
            score += PASSED_CP[rank if color == chess.WHITE else 7 - rank]
    return score


def pawn_structure(board: chess.Board) -> int:
    # White minus Black, in centipawns: doubled and isolated pawns cost, passed pawns pay.
    # shortcut: no backward, connected or protected-passer terms.
    return _side(board, chess.WHITE) - _side(board, chess.BLACK)
