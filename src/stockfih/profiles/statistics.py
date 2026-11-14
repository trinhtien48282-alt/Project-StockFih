from dataclasses import dataclass

from stockfih.profiles.player import GameRecord


def outcome_for(result: str, color: str) -> str | None:
    # "win" / "loss" / "draw" for the profile, or None when it cannot be told
    # (decisive result but no recorded color, or an unfinished result).
    if result == "1/2-1/2":
        return "draw"
    if color not in ("white", "black") or result not in ("1-0", "0-1"):
        return None
    won = (result == "1-0") == (color == "white")
    return "win" if won else "loss"


@dataclass(frozen=True)
class Stats:
    total: int
    wins: int
    losses: int
    draws: int

    @property
    def unscored(self) -> int:
        return self.total - self.wins - self.losses - self.draws

    @property
    def win_rate(self) -> float | None:
        # Wins over scored games (draws count as games). None until there is one.
        scored = self.wins + self.losses + self.draws
        return self.wins / scored if scored else None


def compute(games: list[GameRecord]) -> Stats:
    outcomes = [outcome_for(g.result, g.color) for g in games]
    return Stats(
        total=len(games),
        wins=outcomes.count("win"),
        losses=outcomes.count("loss"),
        draws=outcomes.count("draw"),
    )
