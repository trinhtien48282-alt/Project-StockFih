from stockfih.services import chesscom
from stockfih.services.chesscom import LeaderEntry
from stockfih.ui.leaderboard_dialog import row_values

BOARDS_JSON = {
    "live_blitz": [
        {"rank": 2, "username": "Bob", "score": 3300, "country": "https://api.chess.com/pub/country/NO",
         "win_count": 10, "loss_count": 2, "draw_count": 1, "title": "GM", "name": "Bob B"},
        {"rank": 1, "username": "Ann", "score": 3400, "country": "nonsense", "win_count": "many"},
        {"rank": 3, "score": 3200},  # no username: dropped
        {"rank": True, "username": "Cat", "score": 3100},  # bool rank: dropped
        "junk",
    ],
    "live_bullet": "not a list",
    # live_rapid missing
}


def test_leaderboards_parsed_sorted_and_validated(monkeypatch):
    calls = []
    monkeypatch.setattr(chesscom, "_get_json", lambda path: calls.append(path) or BOARDS_JSON)
    boards = chesscom.fetch_leaderboards()
    assert calls == ["/leaderboards"]
    assert list(boards) == ["live_bullet", "live_blitz", "live_rapid"]
    assert boards["live_bullet"] == [] and boards["live_rapid"] == []
    ann, bob = boards["live_blitz"]
    assert (ann.rank, ann.username, ann.score) == (1, "Ann", 3400)
    assert (ann.country, ann.wins, ann.title) == (None, None, None)  # bad values are dropped
    assert (bob.country, bob.wins, bob.losses, bob.draws, bob.title) == ("NO", 10, 2, 1, "GM")


def test_row_values_with_and_without_title():
    e = LeaderEntry(1, "Ann", 3400, None, None, None, None, None, None)
    assert row_values(e) == ("1", "Ann", "3400", "-", "-", "-", "-")
    g = LeaderEntry(2, "Bob", 3300, "GM", "Bob B", "NO", 10, 2, 1)
    assert row_values(g) == ("2", "GM Bob", "3300", "10", "2", "1", "NO")
