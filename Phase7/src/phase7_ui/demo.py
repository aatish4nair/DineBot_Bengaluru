from __future__ import annotations

from .models import RecommendationView, RestaurantView


def demo_recommendation() -> RecommendationView:
    main = RestaurantView(
        name="Cafe Roma",
        location="Pune",
        price=2,
        rating=4.4,
        cuisine="Italian, Cafe",
    )
    alts = [
        RestaurantView(
            name="Bistro One",
            location="Pune",
            price=2,
            rating=4.2,
            cuisine="Italian",
        ),
        RestaurantView(
            name="Spice Hub",
            location="Pune",
            price=3,
            rating=4.1,
            cuisine="Indian",
        ),
    ]
    return RecommendationView(
        recommended_restaurant=main,
        rationale="Best match for your cuisines and budget (demo response).",
        alternatives=alts,
    )
