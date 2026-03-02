from __future__ import annotations

from dataclasses import dataclass

from .models import Restaurant, UserPreferences


def _normalize_token(value: str) -> str:
    return value.strip().casefold()


def _normalize_tokens(values: list[str]) -> set[str]:
    return {_normalize_token(value) for value in values if value.strip()}


def _place_matches(user_place: str, restaurant_place: str) -> bool:
    """Match place flexibly: exact match or user place is prefix of restaurant place (e.g. Pune matches Pune, Maharashtra)."""
    up = _normalize_token(user_place)
    rp = _normalize_token(restaurant_place)
    if up == rp:
        return True
    # Handle "Pune" matching "Pune, Maharashtra" or "Pune City"
    if rp.startswith(up + ",") or rp.startswith(up + " "):
        return True
    if up in rp.split(",")[0].strip():
        return True
    return False


def filter_restaurants(
    restaurants: list[Restaurant], preferences: UserPreferences
) -> list[Restaurant]:
    place_token = _normalize_token(preferences.place)
    cuisine_tokens = _normalize_tokens(preferences.cuisines)

    filtered = []
    for restaurant in restaurants:
        if not _place_matches(preferences.place, restaurant.place):
            continue
        if restaurant.price_range != preferences.price_range:
            continue
        if restaurant.rating < preferences.rating_min or restaurant.rating >= preferences.rating_max:
            continue
        if cuisine_tokens:
            restaurant_cuisines = _normalize_tokens(restaurant.cuisines)
            # Exact match or substring match (e.g. "Indian" matches "North Indian")
            matched = bool(cuisine_tokens.intersection(restaurant_cuisines))
            if not matched:
                for ut in cuisine_tokens:
                    for rc in restaurant_cuisines:
                        if ut in rc or rc in ut:
                            matched = True
                            break
                    if matched:
                        break
            if not matched:
                continue
        filtered.append(restaurant)
    return filtered


@dataclass(frozen=True)
class ScoredRestaurant:
    restaurant: Restaurant
    score: float


def rank_restaurants(
    restaurants: list[Restaurant], preferences: UserPreferences, limit: int = 5
) -> list[ScoredRestaurant]:
    if limit <= 0:
        raise ValueError("limit must be positive")

    cuisine_tokens = _normalize_tokens(preferences.cuisines)
    scored: list[ScoredRestaurant] = []

    for restaurant in restaurants:
        restaurant_cuisines = _normalize_tokens(restaurant.cuisines)
        cuisine_overlap = len(cuisine_tokens.intersection(restaurant_cuisines))
        price_fit = max(0, preferences.price_range - restaurant.price_range)
        score = (restaurant.rating * 2.0) + (cuisine_overlap * 1.5) + (price_fit * 0.5)
        scored.append(ScoredRestaurant(restaurant=restaurant, score=score))

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]
