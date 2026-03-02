"""Phase 5 data models for standardized recommendation output."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FormattedRestaurant:
    """Standardized restaurant entry: name, location, price, rating, cuisine."""

    name: str
    location: str
    price: int
    rating: float
    cuisine: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("name must be non-empty")
        if not self.location or not self.location.strip():
            raise ValueError("location must be non-empty")
        if not isinstance(self.price, int) or not 1 <= self.price <= 4:
            raise ValueError("price must be an integer between 1 and 4")
        if not isinstance(self.rating, (int, float)) or not 0 <= float(self.rating) <= 5:
            raise ValueError("rating must be between 0 and 5")
        if not self.cuisine or not self.cuisine.strip():
            raise ValueError("cuisine must be non-empty")


@dataclass(frozen=True)
class FormattedRecommendation:
    """Standardized recommendation: main pick, rationale, and alternatives."""

    recommended_restaurant: FormattedRestaurant
    rationale: str
    alternatives: tuple[FormattedRestaurant, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.rationale or not self.rationale.strip():
            raise ValueError("rationale must be non-empty")
