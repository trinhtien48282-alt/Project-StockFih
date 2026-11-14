import pytest

from stockfih.profiles.player import ProfileStore


@pytest.fixture
def store():
    s = ProfileStore(":memory:")
    yield s
    s.close()


def test_create_and_list(store):
    a = store.create("  Akarui   Chan ")
    b = store.create("Bob")
    assert a.username == "Akarui Chan"
    assert [p.username for p in store.profiles()] == ["Akarui Chan", "Bob"]
    assert a.id != b.id


def test_duplicate_username_ignores_case(store):
    store.create("Alice")
    with pytest.raises(ValueError):
        store.create("aLiCe")
    assert len(store.profiles()) == 1


def test_bad_usernames(store):
    for bad in ("", "   ", "x" * 25):
        with pytest.raises(ValueError):
            store.create(bad)
    assert store.profiles() == []
    assert store.create("x" * 24).username == "x" * 24


def test_rename(store):
    a = store.create("Alice")
    assert store.rename(a.id, "Alicia").username == "Alicia"
    assert store.rename(a.id, "ALICIA").username == "ALICIA"  # own name, other case
    assert [p.username for p in store.profiles()] == ["ALICIA"]


def test_rename_clash_changes_nothing(store):
    a = store.create("Alice")
    store.create("Bob")
    with pytest.raises(ValueError):
        store.rename(a.id, "bob")
    with pytest.raises(ValueError):
        store.rename(a.id, " ")
    assert [p.username for p in store.profiles()] == ["Alice", "Bob"]


def test_prefs_default_overwrite_and_isolation(store):
    a, b = store.create("Alice"), store.create("Bob")
    assert store.pref(a.id, "square") == ""
    assert store.pref(a.id, "square", "Brown") == "Brown"
    store.set_pref(a.id, "square", "Green")
    store.set_pref(a.id, "square", "Blue")
    assert store.pref(a.id, "square") == "Blue"
    assert store.pref(b.id, "square") == ""


def test_games_newest_first_and_per_profile(store):
    a, b = store.create("Alice"), store.create("Bob")
    store.add_game(a.id, "pgn one", "1-0", "Alice", "Bob")
    store.add_game(a.id, "pgn two", "0-1", "Bob", "Alice")
    store.add_game(b.id, "pgn three", "1/2-1/2", "?", "?")
    games = store.games(a.id)
    assert [g.pgn for g in games] == ["pgn two", "pgn one"]
    assert games[0].result == "0-1" and games[0].white == "Bob"
    assert [g.pgn for g in store.games(b.id)] == ["pgn three"]


def test_data_survives_reopen(tmp_path):
    path = tmp_path / "deep" / "stockfih.db"  # parent folders are created
    s = ProfileStore(path)
    p = s.create("Alice")
    s.set_pref(p.id, "sound", "0")
    s.add_game(p.id, "pgn", "1-0", "Alice", "Bob")
    s.close()
    s = ProfileStore(path)
    assert [x.username for x in s.profiles()] == ["Alice"]
    assert s.pref(p.id, "sound") == "0"
    assert len(s.games(p.id)) == 1
    s.close()


def test_game_color_is_stored(store):
    a = store.create("Alice")
    store.add_game(a.id, "p1", "1-0", "A", "B", "black")
    store.add_game(a.id, "p2", "1-0", "A", "B")
    assert [g.color for g in store.games(a.id)] == ["", "black"]


def test_v1_database_is_migrated(tmp_path):
    import sqlite3

    path = tmp_path / "old.db"
    db = sqlite3.connect(path)
    db.executescript(
        "CREATE TABLE profiles (id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE);"
        "CREATE TABLE prefs (profile_id INTEGER NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,"
        " PRIMARY KEY (profile_id, key));"
        "CREATE TABLE games (id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL, played TEXT NOT NULL,"
        " white TEXT NOT NULL, black TEXT NOT NULL, result TEXT NOT NULL, pgn TEXT NOT NULL);"
        "INSERT INTO profiles (id, username) VALUES (1, 'Alice');"
        "INSERT INTO games (profile_id, played, white, black, result, pgn)"
        " VALUES (1, '2026-11-01 10:00', 'A', 'B', '1-0', 'old pgn');"
        "PRAGMA user_version = 1;"
    )
    db.commit()
    db.close()
    s = ProfileStore(path)
    assert [g.color for g in s.games(1)] == [""]  # old game kept, color unknown
    s.add_game(1, "new pgn", "0-1", "A", "B", "white")
    assert len(s.games(1)) == 2
    s.close()
    ProfileStore(path).close()  # reopening a v2 database is fine
