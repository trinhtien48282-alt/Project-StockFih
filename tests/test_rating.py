import pytest

from stockfih.profiles import rating
from stockfih.profiles.player import ProfileStore
from stockfih.profiles.rating import RatingChange


def change(after: float) -> RatingChange:
    return RatingChange(0, "2026-11-14 12:00", 1200.0, 1.0, after - 10, after)


def test_expected_score():
    assert rating.expected(1200, 1200) == 0.5
    assert rating.expected(1600, 1200) == pytest.approx(0.9091, abs=1e-4)
    assert rating.expected(1200, 1600) == pytest.approx(0.0909, abs=1e-4)


def test_update_win_draw_loss_equal_ratings():
    assert rating.update(1200, 1200, 1.0, 0) == 1220
    assert rating.update(1200, 1200, 0.5, 0) == 1200
    assert rating.update(1200, 1200, 0.0, 0) == 1180


def test_k_factor_drops_after_new_games():
    assert rating.update(1200, 1200, 1.0, rating.NEW_GAMES - 1) == 1220
    assert rating.update(1200, 1200, 1.0, rating.NEW_GAMES) == 1210


def test_current_and_peak_need_enough_games():
    few = [change(1210 + i) for i in range(rating.PROVISIONAL_GAMES - 1)]
    assert rating.current(few) is None and rating.peak(few) is None
    enough = few + [change(1300), change(1250)]
    assert rating.current(enough) == 1250
    assert rating.peak(enough) == 1300
    # a high rating from before it became visible does not count as the peak
    early_high = [change(1500)] + [change(1200)] * rating.PROVISIONAL_GAMES
    assert rating.peak(early_high) == 1200


def test_store_records_chain_per_profile_and_rejects_bad_input():
    store = ProfileStore(":memory:")
    a, b = store.create("Alice"), store.create("Bob")
    first = store.add_rated_result(a.id, 1200, 1.0)
    second = store.add_rated_result(a.id, 1200, 0.0)
    assert (first.before, first.after) == (1200, 1220)
    assert second.before == first.after
    assert second.after == pytest.approx(1220 + 40 * (0 - rating.expected(1220, 1200)))
    assert [c.after for c in store.rating_history(a.id)] == [first.after, second.after]
    assert store.rating_history(b.id) == []
    for bad_score, bad_opp in ((0.7, 1200), (1.0, 0), (1.0, -5)):
        with pytest.raises(ValueError):
            store.add_rated_result(a.id, bad_opp, bad_score)
    assert len(store.rating_history(a.id)) == 2
    store.close()
