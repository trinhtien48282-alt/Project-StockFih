import chess

HOME_CP = 10  # per knight or bishop still on its starting square. Tune in Phase 14.
EARLY_QUEEN_CP = 15  # queen already left d1/d8 while 2 or more minor pieces are still at home.


def _undeveloped(board: chess.Board, color: chess.Color) -> int:
    rank = 0 if color == chess.WHITE else 7
    count = 0
    for piece, files in ((chess.KNIGHT, (1, 6)), (chess.BISHOP, (2, 5))):
        pieces = board.pieces(piece, color)
        count += sum(chess.square(f, rank) in pieces for f in files)
    return count


def _side(board: chess.Board, color: chess.Color) -> int:
    home = chess.square(3, 0 if color == chess.WHITE else 7)  # d1 or d8
    queens = board.pieces(chess.QUEEN, color)
    count = _undeveloped(board, color)
    score = -HOME_CP * count
    if queens and home not in queens and count >= 2:
        score -= EARLY_QUEEN_CP
    return score


def development(board: chess.Board) -> int:
    # White minus Black, in centipawns. Opening only: off once queens are gone (same
    # middlegame test as pst.py and king_safety.py).
    # shortcut: judged from piece squares, not move number, so a position loaded from a
    # FEN with pieces at home counts as undeveloped. Rooks and castling are not scored here.
    if not board.queens:
        return 0
    return _side(board, chess.WHITE) - _side(board, chess.BLACK)
