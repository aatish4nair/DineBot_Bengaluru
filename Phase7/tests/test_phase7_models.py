import pytest

from phase7_ui.models import RecommendationView, RestaurantView


def test_restaurant_view_from_dict_canonical_keys() -> None:
    r = RestaurantView.from_dict(
        {"name": "Cafe Roma", "location": "Pune", "price": 2, "rating": 4.4, "cuisine": "Italian"}
    )
    assert r.name == "Cafe Roma"
    assert r.location == "Pune"
    assert r.price == 2
    assert r.rating == 4.4
    assert r.cuisine == "Italian"


def test_restaurant_view_from_dict_alternate_keys() -> None:
    r = RestaurantView.from_dict(
        {
            "restaurant_name": "Spice Hub",
            "place": "Mumbai",
            "price_range": 3,
            "aggregate_rating": 4.2,
            "cuisines": ["Indian", "North Indian"],
        }
    )
    assert r.name == "Spice Hub"
    assert r.location == "Mumbai"
    assert r.price == 3
    assert r.rating == 4.2
    assert "Indian" in r.cuisine


def test_recommendation_view_from_dict() -> None:
    view = RecommendationView.from_dict(
        {
            "recommended_restaurant": {
                "name": "Cafe Roma",
                "location": "Pune",
                "price": 2,
                "rating": 4.4,
                "cuisine": "Italian, Cafe",
            },
            "rationale": "Great fit.",
            "alternatives": [
                {"name": "Bistro One", "location": "Pune", "price": 2, "rating": 4.2, "cuisine": "Italian"}
            ],
        }
    )
    assert view.recommended_restaurant.name == "Cafe Roma"
    assert view.rationale == "Great fit."
    assert len(view.alternatives) == 1
    assert view.alternatives[0].name == "Bistro One"

