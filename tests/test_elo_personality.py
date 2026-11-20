import pytest

from stockfih.personality.elo_personality import Tier, rating_difference, tier_for, tier_for_difference

T = Tier


@pytest.mark.parametrize(
    "difference, expected",
    [
        (-1000, T.DOMINANT),
        (-300, T.DOMINANT),
        (-299, T.COCKY),
        (-100, T.COCKY),
        (-99, T.RIVAL),
        (0, T.RIVAL),
        (99, T.RIVAL),
        (100, T.THREATENED),
        (299, T.THREATENED),
        (300, T.EXISTENTIAL_CRISIS),
        (1000, T.EXISTENTIAL_CRISIS),
    ],
)
def test_roadmap_boundaries(difference, expected):
    assert tier_for_difference(difference) is expected


def test_fractional_gaps_land_in_a_tier():
    assert tier_for_difference(-99.5) is T.RIVAL
    assert tier_for_difference(-100.5) is T.COCKY
    assert tier_for_difference(99.9) is T.RIVAL
    assert tier_for_difference(299.9) is T.THREATENED


def test_difference_is_player_minus_stockfih():
    assert rating_difference(1500, 1200) == 300
    assert rating_difference(1000, 1200) == -200


def test_weaker_player_means_stockfih_is_dominant():
    assert tier_for(800, 1500) is T.DOMINANT


def test_much_stronger_player_means_existential_crisis():
    assert tier_for(2000, 1500) is T.EXISTENTIAL_CRISIS


def test_similar_ratings_are_rivals():
    assert tier_for(1500, 1500) is T.RIVAL


def test_unknown_rating_gives_no_tier():
    assert tier_for(None, 1500) is None
    assert tier_for(1500, None) is None
    assert tier_for(None, None) is None


@pytest.mark.parametrize("bad", [0, -5, float("nan"), float("inf"), True, "1500"])
def test_bad_ratings_are_refused(bad):
    with pytest.raises(ValueError):
        tier_for(bad, 1500)
    with pytest.raises(ValueError):
        tier_for(1500, bad)


def test_tier_values_are_the_dialogue_keys():
    assert [t.value for t in Tier] == ["dominant", "cocky", "rival", "threatened", "existential_crisis"]
