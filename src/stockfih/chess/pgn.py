import io
from datetime import date

import chess
import chess.pgn


def default_headers() -> dict[str, str]:
    return {
        "Event": "StockFih game",
        "Date": date.today().strftime("%Y.%m.%d"),
        "White": "?",
        "Black": "?",
    }


def export_pgn(
    board: chess.Board,
    upcoming: list[chess.Move],
    headers: dict[str, str],
    result: str,
) -> str:
    # board.move_stack is the line played so far; `upcoming` are moves after it (in order).
    game = chess.pgn.Game.from_board(board)
    for key, value in headers.items():
        game.headers[key] = value
    game.headers["Result"] = result
    node = game.end()
    for move in upcoming:
        node = node.add_variation(move)
    return str(game) + "\n"


def import_pgn(text: str) -> tuple[chess.Board, list[chess.Move], dict[str, str]]:
    # First game only, main line only. Strict: any illegal move rejects the whole PGN.
    game = chess.pgn.read_game(io.StringIO(text))
    if game is None:
        raise ValueError("No game found in this PGN.")
    if game.errors:
        raise ValueError(f"Invalid PGN: {game.errors[0]}")
    board = game.board()  # ValueError on a bad FEN or unsupported variant
    return board, list(game.mainline_moves()), dict(game.headers)
