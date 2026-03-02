from dataclasses import dataclass, field


@dataclass(frozen=True)
class UserPreferences:
    place: str
    price_range: int
    rating_min: float
    rating_max: float
    cuisines: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Restaurant:
    restaurant_name: str
    place: str
    price_range: int
    rating: float
    cuisines: list[str]
