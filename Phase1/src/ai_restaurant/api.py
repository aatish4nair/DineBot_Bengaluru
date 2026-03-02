from .contracts import RecommendationResponse, UserPreferences


def recommend(preferences: UserPreferences) -> RecommendationResponse:
    raise NotImplementedError(
        "Phase 1 only: recommendation pipeline not implemented yet."
    )
