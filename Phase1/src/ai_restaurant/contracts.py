from dataclasses import dataclass, field


DATASET_FIELD_MAPPING = {
    "place": "City",
    "price_range": "Price range",
    "rating": "Aggregate rating",
    "cuisines": "Cuisines",
    "restaurant_name": "Restaurant Name",
    "address": "Address",
}


@dataclass(frozen=True)
class UserPreferences:
    place: str
    price_range: int
    min_rating: float
    cuisines: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.place or not self.place.strip():
            raise ValueError("place must be a non-empty string")
        if not isinstance(self.price_range, int) or not 1 <= self.price_range <= 4:
            raise ValueError("price_range must be an integer between 1 and 4")
        if not isinstance(self.min_rating, (int, float)) or not 0 <= self.min_rating <= 5:
            raise ValueError("min_rating must be between 0 and 5")
        if not self.cuisines:
            raise ValueError("cuisines must include at least one cuisine")
        for cuisine in self.cuisines:
            if not cuisine or not cuisine.strip():
                raise ValueError("cuisines must contain non-empty strings")


@dataclass(frozen=True)
class RecommendationCandidate:
    restaurant_name: str
    location: str
    price_range: int
    rating: float
    cuisines: list[str]


@dataclass(frozen=True)
class RecommendationResponse:
    recommended_restaurant: RecommendationCandidate
    rationale: str
    alternatives: list[RecommendationCandidate] = field(default_factory=list)
