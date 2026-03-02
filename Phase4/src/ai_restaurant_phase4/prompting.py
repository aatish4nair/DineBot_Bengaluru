from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateContext:
    restaurant_name: str
    location: str
    price_range: int
    rating: float
    cuisines: list[str]


def build_prompt(
    preferences: dict[str, object], candidates: list[CandidateContext]
) -> str:
    candidate_lines = []
    for index, candidate in enumerate(candidates, start=1):
        cuisines = ", ".join(candidate.cuisines)
        candidate_lines.append(
            f"{index}. {candidate.restaurant_name} | {candidate.location} | "
            f"price {candidate.price_range} | rating {candidate.rating} | "
            f"cuisines: {cuisines}"
        )

    preference_lines = [
        f"place: {preferences.get('place')}",
        f"price_range: {preferences.get('price_range')}",
        f"rating_range: {preferences.get('rating_min')}-{preferences.get('rating_max')}",
        f"cuisines: {preferences.get('cuisines')}",
    ]

    return (
        "You are an assistant that recommends a restaurant based on user preferences.\n"
        "User preferences:\n"
        + "\n".join(preference_lines)
        + "\n\nCandidates:\n"
        + ("\n".join(candidate_lines) if candidate_lines else "None")
        + "\n\nReturn a single recommended restaurant with a short rationale."
    )
