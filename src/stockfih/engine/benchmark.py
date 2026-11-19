from dataclasses import dataclass

import chess

from stockfih.engine.stockfih import StockFihEngine

# Fixed positions, so numbers can be compared between versions. Speed and search size only:
# this measures nothing about playing strength. No ELO claim comes from here.
POSITIONS = (
    ("Start", chess.STARTING_FEN),
    ("Kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("Endgame", "8/2k5/4p3/3P4/6K1/8/8/6K1 w - - 0 1"),
    ("Tactics", "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"),
    ("Middlegame", "r2q1rk1/ppp2ppp/2n1bn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9"),
)


@dataclass(frozen=True)
class BenchResult:
    name: str
    depth: int  # depth asked for
    reached_depth: int  # deepest pass that finished
    move: str  # SAN of the move chosen
    nodes: int
    seconds: float
    nps: float | None  # None when no time was measured
    timed_out: bool


def run(depth: int = 3, positions: tuple[tuple[str, str], ...] = POSITIONS) -> list[BenchResult]:
    # A fresh engine per position, so transposition-table entries from one position cannot
    # make the next one look faster.
    results = []
    for name, fen in positions:
        engine = StockFihEngine(depth=depth, seed=1)
        board = chess.Board(fen)
        move = engine.choose_move(board)
        stats = engine.stats
        results.append(
            BenchResult(
                name=name,
                depth=depth,
                reached_depth=engine.reached_depth,
                move=board.san(move),
                nodes=stats.nodes,
                seconds=stats.seconds,
                nps=stats.nps,
                timed_out=stats.timed_out,
            )
        )
    return results


def format_table(results: list[BenchResult]) -> str:
    header = f"{'Position':<12}{'Depth':>6}{'Reached':>8}{'Move':>9}{'Nodes':>10}{'Seconds':>9}{'Nodes/s':>10}"
    lines = [header, "-" * len(header)]
    for r in results:
        nps = "-" if r.nps is None else f"{r.nps:.0f}"
        flag = "  (time/node limit)" if r.timed_out else ""
        lines.append(
            f"{r.name:<12}{r.depth:>6}{r.reached_depth:>8}{r.move:>9}"
            f"{r.nodes:>10}{r.seconds:>9.2f}{nps:>10}{flag}"
        )
    return "\n".join(lines)
