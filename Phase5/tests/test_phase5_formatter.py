"""Phase 5 tests: standardized recommendation format, rationale, alternatives."""

import pytest

from ai_restaurant_phase5 import (
    FormattedRecommendation,
    FormattedRestaurant,
    format_recommendation,
)


def _sample_restaurant(
    name: str = "Cafe Roma",
    location: str = "Pune",
    price: int = 2,
    rating: float = 4.4,
    cuisine: str = "Italian, Cafe",
) -> dict:
    return {
        "name": name,
        "location": location,
        "price": price,
        "rating": rating,
        "cuisine": cuisine,
    }


def _sample_restaurant_alt_keys() -> dict:
    """Dict using alternate keys (restaurant_name, place, price_range, cuisines)."""
    return {
        "restaurant_name": "Spice Hub",
        "place": "Mumbai",
        "price_range": 3,
        "rating": 4.2,
        "cuisines": ["Indian", "North Indian"],
    }


def test_formatted_restaurant_valid() -> None:
    r = FormattedRestaurant(name="X", location="Y", price=2, rating=4.0, cuisine="Thai")
    assert r.name == "X"
    assert r.location == "Y"
    assert r.price == 2
    assert r.rating == 4.0
    assert r.cuisine == "Thai"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": ""},
        {"location": ""},
        {"price": 0},
        {"price": 5},
        {"rating": -0.1},
        {"rating": 5.1},
        {"cuisine": ""},
    ],
)
def test_formatted_restaurant_validation_fails(kwargs: dict) -> None:
    base = {"name": "A", "location": "B", "price": 1, "rating": 3.0, "cuisine": "X"}
    base.update(kwargs)
    with pytest.raises(ValueError):
        FormattedRestaurant(**base)


def test_formatted_recommendation_requires_rationale() -> None:
    r = FormattedRestaurant(name="A", location="B", price=1, rating=3.0, cuisine="Y")
    with pytest.raises(ValueError, match="rationale"):
        FormattedRecommendation(recommended_restaurant=r, rationale="")
    with pytest.raises(ValueError, match="rationale"):
        FormattedRecommendation(recommended_restaurant=r, rationale="   ")


def test_format_recommendation_standard_shape() -> None:
    rec = format_recommendation(
        recommended=_sample_restaurant(),
        rationale="Great fit for your Italian preference and budget.",
        alternatives=[
            _sample_restaurant(name="Bistro One", rating=4.2),
            _sample_restaurant(name="Trattoria", location="Mumbai", price=3),
        ],
    )
    assert isinstance(rec, FormattedRecommendation)
    assert rec.recommended_restaurant.name == "Cafe Roma"
    assert rec.recommended_restaurant.location == "Pune"
    assert rec.recommended_restaurant.price == 2
    assert rec.recommended_restaurant.rating == 4.4
    assert rec.recommended_restaurant.cuisine == "Italian, Cafe"
    assert "Italian" in rec.rationale
    assert len(rec.alternatives) == 2
    assert rec.alternatives[0].name == "Bistro One"
    assert rec.alternatives[1].name == "Trattoria"


def test_format_recommendation_alternate_keys() -> None:
    rec = format_recommendation(
        recommended=_sample_restaurant_alt_keys(),
        rationale="Matches your Indian cuisine choice.",
    )
    assert rec.recommended_restaurant.name == "Spice Hub"
    assert rec.recommended_restaurant.location == "Mumbai"
    assert rec.recommended_restaurant.price == 3
    assert rec.recommended_restaurant.rating == 4.2
    assert "Indian" in rec.recommended_restaurant.cuisine
    assert rec.alternatives == ()


def test_format_recommendation_empty_alternatives() -> None:
    rec = format_recommendation(
        recommended=_sample_restaurant(),
        rationale="Only one match.",
        alternatives=[],
    )
    assert len(rec.alternatives) == 0


def test_format_recommendation_none_alternatives() -> None:
    rec = format_recommendation(
        recommended=_sample_restaurant(),
        rationale="Single recommendation.",
        alternatives=None,
    )
    assert len(rec.alternatives) == 0


def test_format_recommendation_empty_rationale_raises() -> None:
    with pytest.raises(ValueError, match="rationale"):
        format_recommendation(
            recommended=_sample_restaurant(),
            rationale="",
        )
    with pytest.raises(ValueError, match="rationale"):
        format_recommendation(
            recommended=_sample_restaurant(),
            rationale="   ",
        )


def test_cuisine_from_list() -> None:
    rec = format_recommendation(
        recommended={
            "name": "Fusion",
            "location": "Delhi",
            "price": 2,
            "rating": 4.5,
            "cuisines": ["Indian", "Chinese"],
        },
        rationale="Good mix.",
    )
    assert "Indian" in rec.recommended_restaurant.cuisine
    assert "Chinese" in rec.recommended_restaurant.cuisine


def test_cuisine_missing_defaults_to_placeholder() -> None:
    rec = format_recommendation(
        recommended={
            "name": "N",
            "location": "L",
            "price": 1,
            "rating": 3.0,
        },
        rationale="No cuisine listed.",
    )
    assert rec.recommended_restaurant.cuisine == "—"
