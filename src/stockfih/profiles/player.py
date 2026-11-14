import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE
);
CREATE TABLE IF NOT EXISTS prefs (
    profile_id INTEGER NOT NULL REFERENCES profiles(id),
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (profile_id, key)
);
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    profile_id INTEGER NOT NULL REFERENCES profiles(id),
    played TEXT NOT NULL,
    white TEXT NOT NULL,
    black TEXT NOT NULL,
    result TEXT NOT NULL,
    pgn TEXT NOT NULL,
    color TEXT NOT NULL DEFAULT ''
);
"""


@dataclass(frozen=True)
class Profile:
    id: int
    username: str


@dataclass(frozen=True)
class GameRecord:
    id: int
    played: str
    white: str
    black: str
    result: str
    pgn: str
    color: str  # side the profile played: "white", "black", or "" if unknown


def _username(value: str) -> str:
    name = " ".join(value.split())
    if not 1 <= len(name) <= 24:
        raise ValueError("Username must be 1 to 24 characters.")
    return name


class ProfileStore:
    # Profiles, per-profile preferences and finished-game history in one SQLite file.
    # Pass ":memory:" for a throwaway database (tests).
    def __init__(self, path: Path | str) -> None:
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path)
        version = self._db.execute("PRAGMA user_version").fetchone()[0]
        if version == 1:  # v1 had no color column on games
            self._db.execute("ALTER TABLE games ADD COLUMN color TEXT NOT NULL DEFAULT ''")
        self._db.executescript(_SCHEMA + "PRAGMA user_version = 2;")

    def close(self) -> None:
        self._db.close()

    def profiles(self) -> list[Profile]:
        rows = self._db.execute("SELECT id, username FROM profiles ORDER BY id")
        return [Profile(*row) for row in rows]

    def create(self, username: str) -> Profile:
        # Raises ValueError if the name is invalid or already taken (ignoring case).
        name = _username(username)
        try:
            with self._db:
                cursor = self._db.execute("INSERT INTO profiles (username) VALUES (?)", (name,))
        except sqlite3.IntegrityError:
            raise ValueError(f'Username "{name}" is already taken.') from None
        return Profile(cursor.lastrowid, name)

    def rename(self, profile_id: int, username: str) -> Profile:
        # Raises ValueError and changes nothing if the name is invalid or taken.
        name = _username(username)
        try:
            with self._db:
                self._db.execute("UPDATE profiles SET username = ? WHERE id = ?", (name, profile_id))
        except sqlite3.IntegrityError:
            raise ValueError(f'Username "{name}" is already taken.') from None
        return Profile(profile_id, name)

    def pref(self, profile_id: int, key: str, default: str = "") -> str:
        row = self._db.execute(
            "SELECT value FROM prefs WHERE profile_id = ? AND key = ?", (profile_id, key)
        ).fetchone()
        return row[0] if row else default

    def set_pref(self, profile_id: int, key: str, value: str) -> None:
        with self._db:
            self._db.execute(
                "INSERT INTO prefs (profile_id, key, value) VALUES (?, ?, ?) "
                "ON CONFLICT (profile_id, key) DO UPDATE SET value = excluded.value",
                (profile_id, key, value),
            )

    def add_game(
        self, profile_id: int, pgn: str, result: str, white: str, black: str, color: str = ""
    ) -> None:
        played = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._db:
            self._db.execute(
                "INSERT INTO games (profile_id, played, white, black, result, pgn, color) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (profile_id, played, white, black, result, pgn, color),
            )

    def games(self, profile_id: int) -> list[GameRecord]:
        # Newest first.
        rows = self._db.execute(
            "SELECT id, played, white, black, result, pgn, color FROM games "
            "WHERE profile_id = ? ORDER BY id DESC",
            (profile_id,),
        )
        return [GameRecord(*row) for row in rows]
