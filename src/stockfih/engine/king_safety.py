import chess

SHIELD_CP = 10  # centipawns per friendly pawn in the shield zone. Tune in Phase 14.


def _shield(board: chess.Board, color: chess.Color) -> int:
    # Friendly pawns on the king's file and the two files beside it, on the 2 ranks in front.
    king = board.king(color)
    if king is None:
        return 0
    file, rank = chess.square_file(king), chess.square_rank(king)
    step = 1 if color == chess.WHITE else -1
    pawns = board.pieces(chess.PAWN, color)
    count = 0
    for r in (rank + step, rank + 2 * step):
        if not 0 <= r <= 7:
            continue
        for f in (file - 1, file, file + 1):
            if 0 <= f <= 7 and chess.square(f, r) in pawns:
                count += 1
    return SHIELD_CP * count


def king_safety(board: chess.Board) -> int:
    # White minus Black, in centipawns. Pawn shield only, and only while queens are on the
    # board (same middlegame test the king table uses in pst.py).
    # shortcut: no attacker counting and no open-file check near the king. Upgrade when tuning.
    if not board.queens:
        return 0
    return _shield(board, chess.WHITE) - _shield(board, chess.BLACK)
