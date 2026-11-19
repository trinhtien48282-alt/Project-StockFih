# Prints the engine benchmark table. Run from the project root:
#   uv run python scripts\benchmark.py --depth 3
import argparse
import sys

from stockfih.engine.benchmark import format_table, run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="StockFih engine benchmark (speed and search size).")
    parser.add_argument("--depth", type=int, default=3, help="search depth in plies (default 3)")
    args = parser.parse_args(argv)
    if args.depth < 1:
        parser.error("depth must be at least 1")
    print(format_table(run(args.depth)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
