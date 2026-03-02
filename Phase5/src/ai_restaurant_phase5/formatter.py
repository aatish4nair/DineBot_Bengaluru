"""Phase 5 response formatting: standardized recommendation with rationale and alternatives."""

from .models import FormattedRecommendation, FormattedRestaurant


def _normalize_cuisine(cuisines: str | list[str]) -> str:
    """Turn cuisines into a single comma-separated string."""
    if isinstance(cuisines, list):
        return ", ".join(str(c).strip() for c in cuisines if c)
    return str(cuisines).strip() if cuisines else ""


def _to_formatted_restaurant(raw: dict) -> FormattedRestaurant:
    """Build FormattedRestaurant from a dict with name, location, price_range, rating, cuisines."""
    name = str(raw.get("name", raw.get("restaurant_name", ""))).strip() or "—"
    location = str(raw.get("location", raw.get("place", raw.get("address", "")))).strip() or "—"
    price = int(raw.get("price", raw.get("price_range", 1)))
    rating = float(raw.get("rating", raw.get("aggregate_rating", 0)))
    cuisine = _normalize_cuisine(raw.get("cuisine", raw.get("cuisines", "")))
    if not cuisine:
        cuisine = "—"
    return FormattedRestaurant(name=name, location=location, price=price, rating=rating, cuisine=cuisine)


def format_recommendation(
    recommended: dict,
    rationale: str,
    alternatives: list[dict] | None = None,
) -> FormattedRecommendation:
    """
    Produce a standardized recommendation (name, location, price, rating, cuisine)
    with concise rationale and optional alternatives.
    """
    if not rationale or not rationale.strip():
        raise ValueError("rationale must be non-empty")
    main = _to_formatted_restaurant(recommended)
    alt_list = alternatives or []
    formatted_alternatives = tuple(_to_formatted_restaurant(a) for a in alt_list)
    return FormattedRecommendation(
        recommended_restaurant=main,
        rationale=rationale.strip(),
        alternatives=formatted_alternatives,
    )
