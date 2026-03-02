import pytest

from ai_restaurant_phase3.filtering import filter_restaurants, rank_restaurants
from ai_restaurant_phase3.models import Restaurant, UserPreferences


def _restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            restaurant_name="Cafe Roma",
            place="Pune",
            price_range=2,
            rating=4.4,
            cuisines=["Italian", "Cafe"],
        ),
        Restaurant(
            restaurant_name="Spice Hub",
            place="Pune",
            price_range=3,
            rating=4.1,
            cuisines=["Indian"],
        ),
        Restaurant(
            restaurant_name="Budget Bites",
            place="Pune",
            price_range=1,
            rating=3.6,
            cuisines=["Fast Food"],
        ),
        Restaurant(
            restaurant_name="Sea Breeze",
            place="Mumbai",
            price_range=2,
            rating=4.5,
            cuisines=["Seafood"],
        ),
    ]


def test_filter_restaurants_matches_preferences() -> None:
    prefs = UserPreferences(
        place="Pune",
        price_range=2,
        rating_min=4.0,
        rating_max=5.5,
        cuisines=["Italian"],
    )
    result = filter_restaurants(_restaurants(), prefs)
    assert [item.restaurant_name for item in result] == ["Cafe Roma"]


def test_filter_restaurants_allows_multiple_cuisines() -> None:
    prefs = UserPreferences(
        place="Pune",
        price_range=3,
        rating_min=3.5,
        rating_max=5.5,
        cuisines=["Indian", "Fast Food"],
    )
    result = filter_restaurants(_restaurants(), prefs)
    # Spice Hub: price 3, Indian, rating 4.1; Budget Bites: price 1 (excluded by exact price match)
    assert [r.restaurant_name for r in result] == ["Spice Hub"]


def test_filter_restaurants_case_insensitive() -> None:
    prefs = UserPreferences(
        place=" pune ",
        price_range=2,
        rating_min=4.0,
        rating_max=5.5,
        cuisines=["italian"],
    )
    result = filter_restaurants(_restaurants(), prefs)
    assert [item.restaurant_name for item in result] == ["Cafe Roma"]


def test_rank_restaurants_orders_by_score() -> None:
    prefs = UserPreferences(
        place="Pune",
        price_range=3,
        rating_min=3.0,
        rating_max=5.5,
        cuisines=["Indian", "Fast Food"],
    )
    filtered = filter_restaurants(_restaurants(), prefs)
    # Only Spice Hub matches (price 3, Indian/Fast Food cuisine match, rating 4.1)
    ranked = rank_restaurants(filtered, prefs, limit=2)
    assert len(ranked) >= 1
    assert ranked[0].restaurant.restaurant_name == "Spice Hub"


def test_rank_restaurants_respects_limit() -> None:
    prefs = UserPreferences(
        place="Pune",
        price_range=3,
        rating_min=3.0,
        rating_max=5.5,
        cuisines=["Indian", "Fast Food", "Italian"],
    )
    filtered = filter_restaurants(_restaurants(), prefs)
    ranked = rank_restaurants(filtered, prefs, limit=1)
    assert len(ranked) == 1


def test_rank_restaurants_invalid_limit() -> None:
    prefs = UserPreferences(
        place="Pune",
        price_range=2,
        rating_min=3.0,
        rating_max=5.5,
        cuisines=["Italian"],
    )
    filtered = filter_restaurants(_restaurants(), prefs)
    with pytest.raises(ValueError, match="limit must be positive"):
        rank_restaurants(filtered, prefs, limit=0)
