# Runs StockFih on the tactical puzzle set. Run from the project root:
#   uv run python scripts\puzzles.py --depth 3
import argparse
import sys

from stockfih.engine.puzzles import format_table, run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="StockFih tactical puzzle check.")
    parser.add_argument("--depth", type=int, default=3, help="search depth in plies (default 3)")
    args = parser.parse_args(argv)
    if args.depth < 1:
        parser.error("depth must be at least 1")
    print(format_table(run(args.depth)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
