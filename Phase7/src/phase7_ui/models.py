from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PreferenceInput:
    place: str
    price_range: int
    rating_min: float
    rating_max: float
    cuisines: list[str] = field(default_factory=list)

    def to_payload(self) -> dict:
        return {
            "place": self.place,
            "price_range": self.price_range,
            "rating_min": self.rating_min,
            "rating_max": self.rating_max,
            "cuisines": self.cuisines,
        }


@dataclass(frozen=True)
class RestaurantView:
    name: str
    location: str
    price: int
    rating: float
    cuisine: str
    rationale: str = ""

    @staticmethod
    def from_dict(d: dict) -> "RestaurantView":
        name = str(d.get("name", d.get("restaurant_name", "—"))).strip() or "—"
        location = str(d.get("location", d.get("place", d.get("address", "—")))).strip() or "—"
        price = int(d.get("price", d.get("price_range", 1)))
        rating = float(d.get("rating", d.get("aggregate_rating", 0.0)))
        cuisine = d.get("cuisine", d.get("cuisines", "—"))
        if isinstance(cuisine, list):
            cuisine = ", ".join(str(x).strip() for x in cuisine if str(x).strip())
        cuisine = str(cuisine).strip() or "—"
        rationale = str(d.get("rationale", "")).strip()
        return RestaurantView(
            name=name,
            location=location,
            price=price,
            rating=rating,
            cuisine=cuisine,
            rationale=rationale,
        )


@dataclass(frozen=True)
class RecommendationView:
    recommended_restaurant: RestaurantView
    rationale: str
    alternatives: list[RestaurantView] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict) -> "RecommendationView":
        recommended = RestaurantView.from_dict(d.get("recommended_restaurant", d.get("recommended", {})) or {})
        rationale = str(d.get("rationale", "")).strip()
        alternatives_raw = d.get("alternatives", []) or []
        alternatives = [RestaurantView.from_dict(x) for x in alternatives_raw if isinstance(x, dict)]
        return RecommendationView(
            recommended_restaurant=recommended,
            rationale=rationale,
            alternatives=alternatives,
        )
