import time
from dataclasses import dataclass


class SearchTimeout(Exception):
    # Raised inside the search when the time or node limit is up. choose_move catches it.
    pass


CHECK_EVERY = 128  # nodes between clock reads. Small: one Python node costs far more than a clock read.


@dataclass
class SearchStats:
    # Filled in by the engine during choose_move. Counts the search itself, nothing estimated.
    # nodes = calls of negamax (past depth 0) and quiescence, over all deepening passes.
    # A pass cut off by the time limit still counts its nodes.
    nodes: int = 0
    seconds: float = 0.0  # wall time of the whole choose_move
    timed_out: bool = False  # True when the time or node limit stopped a deeper pass
    deadline: float | None = None  # time.perf_counter() value to stop at; None = no limit
    node_limit: int | None = None  # stop when `nodes` reaches this; None = no limit

    @property
    def nps(self) -> float | None:
        # Nodes per second. None until there is a measured time.
        return self.nodes / self.seconds if self.seconds > 0 else None

    def tick(self) -> None:
        self.nodes += 1
        if self.node_limit is not None and self.nodes >= self.node_limit:
            raise SearchTimeout
        if (
            self.deadline is not None
            and self.nodes % CHECK_EVERY == 0
            and time.perf_counter() > self.deadline
        ):
            raise SearchTimeout
