# Plays StockFih (A) against StockFih (B) at different depths. Run from the project root:
#   uv run python scripts\match.py --a-depth 2 --b-depth 1
# Shows who scored more over a few games. It is NOT an ELO measurement.
import argparse
import sys

from stockfih.engine.match import OPENINGS, GameResult, play_match, summarize
from stockfih.engine.stockfih import StockFihEngine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="StockFih self-match at two search depths.")
    parser.add_argument("--a-depth", type=int, default=2)
    parser.add_argument("--b-depth", type=int, default=1)
    parser.add_argument("--openings", type=int, default=len(OPENINGS), help="how many openings (2 games each)")
    parser.add_argument("--max-plies", type=int, default=200)
    args = parser.parse_args(argv)
    if args.a_depth < 1 or args.b_depth < 1:
        parser.error("depths must be at least 1")
    if not 1 <= args.openings <= len(OPENINGS):
        parser.error(f"openings must be 1 to {len(OPENINGS)}")

    def show(game: GameResult) -> None:
        color = "White" if game.a_is_white else "Black"
        note = "  (ply cap, scored as draw)" if game.adjudicated else ""
        print(f"opening {game.opening + 1}  A={color}  {game.result:<8}{game.plies:>4} plies{note}", flush=True)

    results = play_match(
        lambda: StockFihEngine(depth=args.a_depth),
        lambda: StockFihEngine(depth=args.b_depth),
        OPENINGS[: args.openings],
        args.max_plies,
        show,
    )
    s = summarize(results)
    print(f"\nA (depth {args.a_depth}) vs B (depth {args.b_depth}): +{s.wins} ={s.draws} -{s.losses}")
    print(f"A score: {s.score:.1%} over {s.games} games, {s.adjudicated} stopped by the ply cap.")
    print("Few games = noisy. This is a comparison, not an ELO.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
