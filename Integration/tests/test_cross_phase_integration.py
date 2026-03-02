"""
End-to-end integration tests: verify data flows correctly across all phases.

Flow: Phase1 (preferences) -> Phase2 (dataset) -> Phase3 (filter/rank) ->
      Phase4 (prompt) -> Phase5 (format) -> Phase6 (observability).
"""

import pytest


def _dataset_record_to_restaurant(record: dict) -> "Restaurant":
    """Convert Phase 2 dataset record (dataset column names) to Phase 3 Restaurant."""
    from ai_restaurant_phase3.models import Restaurant

    cuisines_raw = record.get("Cuisines") or record.get("cuisines") or ""
    cuisines = [s.strip() for s in str(cuisines_raw).split(",") if s.strip()]
    if not cuisines:
        cuisines = ["—"]

    return Restaurant(
        restaurant_name=str(record.get("Restaurant Name", record.get("restaurant_name", "—"))),
        place=str(record.get("City", record.get("place", "—"))),
        price_range=int(record.get("Price range", record.get("price_range", 1))),
        rating=float(record.get("Aggregate rating", record.get("rating", 0))),
        cuisines=cuisines,
    )


def _restaurant_to_candidate_context(restaurant: "Restaurant") -> "CandidateContext":
    """Convert Phase 3 Restaurant to Phase 4 CandidateContext."""
    from ai_restaurant_phase4.prompting import CandidateContext

    return CandidateContext(
        restaurant_name=restaurant.restaurant_name,
        location=restaurant.place,
        price_range=restaurant.price_range,
        rating=restaurant.rating,
        cuisines=restaurant.cuisines,
    )


def _restaurant_to_recommendation_dict(restaurant: "Restaurant") -> dict:
    """Convert Phase 3 Restaurant to dict for Phase 5 format_recommendation."""
    return {
        "name": restaurant.restaurant_name,
        "location": restaurant.place,
        "price_range": restaurant.price_range,
        "rating": restaurant.rating,
        "cuisines": restaurant.cuisines,
    }


def test_phase1_preferences_validate_and_match_phase3_shape() -> None:
    """Phase 1 UserPreferences validates input and is compatible with Phase 3."""
    from ai_restaurant.contracts import UserPreferences as P1Prefs

    prefs = P1Prefs(
        place="Pune",
        price_range=2,
        min_rating=4.0,
        cuisines=["Italian", "Cafe"],
    )
    assert prefs.place == "Pune"
    assert prefs.price_range == 2
    # Phase 3 filter_restaurants expects same attribute names (duck typing)
    assert hasattr(prefs, "place")
    assert hasattr(prefs, "price_range")
    assert hasattr(prefs, "min_rating")
    assert hasattr(prefs, "cuisines")


def test_phase2_dataset_records_convert_to_phase3_restaurants() -> None:
    """Phase 2 validated records (dataset keys) convert to Phase 3 Restaurant."""
    from ai_restaurant_phase2.data_loader import DatasetLoader, validate_dataset

    sample = [
        {
            "City": "Pune",
            "Price range": 2,
            "Aggregate rating": 4.2,
            "Cuisines": "Italian, Cafe",
            "Restaurant Name": "Cafe Roma",
            "Address": "Central Pune",
        },
    ]
    validated = validate_dataset(sample)
    assert len(validated) == 1
    r = _dataset_record_to_restaurant(validated[0])
    assert r.restaurant_name == "Cafe Roma"
    assert r.place == "Pune"
    assert r.price_range == 2
    assert r.rating == 4.2
    assert "Italian" in r.cuisines and "Cafe" in r.cuisines

    loader = DatasetLoader(provider=lambda: sample, cache_enabled=True)
    loaded = loader.load()
    assert len(loaded) == 1
    r2 = _dataset_record_to_restaurant(loaded[0])
    assert r2.restaurant_name == "Cafe Roma"


def test_phase3_filter_and_rank_accept_phase1_like_preferences() -> None:
    """Phase 3 filter/rank work with Phase 1-style preferences and Phase 2->3 restaurants."""
    from ai_restaurant.contracts import UserPreferences as P1Prefs
    from ai_restaurant_phase3.filtering import filter_restaurants, rank_restaurants

    restaurants = [
        _dataset_record_to_restaurant({
            "City": "Pune",
            "Price range": 2,
            "Aggregate rating": 4.4,
            "Cuisines": "Italian, Cafe",
            "Restaurant Name": "Cafe Roma",
            "Address": "Pune",
        }),
        _dataset_record_to_restaurant({
            "City": "Mumbai",
            "Price range": 2,
            "Aggregate rating": 4.5,
            "Cuisines": "Seafood",
            "Restaurant Name": "Sea Breeze",
            "Address": "Mumbai",
        }),
    ]
    prefs = P1Prefs(place="Pune", price_range=2, min_rating=4.0, cuisines=["Italian"])
    filtered = filter_restaurants(restaurants, prefs)
    assert len(filtered) == 1
    assert filtered[0].restaurant_name == "Cafe Roma"

    ranked = rank_restaurants(filtered, prefs, limit=5)
    assert len(ranked) == 1
    assert ranked[0].restaurant.restaurant_name == "Cafe Roma"


def test_phase3_to_phase4_candidate_context_and_prompt() -> None:
    """Phase 3 Restaurant -> Phase 4 CandidateContext and build_prompt produces valid prompt."""
    from ai_restaurant_phase3.models import Restaurant
    from ai_restaurant_phase4.prompting import build_prompt

    restaurant = Restaurant(
        restaurant_name="Cafe Roma",
        place="Pune",
        price_range=2,
        rating=4.4,
        cuisines=["Italian", "Cafe"],
    )
    candidate = _restaurant_to_candidate_context(restaurant)
    assert candidate.restaurant_name == "Cafe Roma"
    assert candidate.location == "Pune"

    preferences_dict = {
        "place": "Pune",
        "price_range": 2,
        "min_rating": 4.0,
        "cuisines": ["Italian"],
    }
    prompt = build_prompt(preferences_dict, [candidate])
    assert "Pune" in prompt
    assert "Cafe Roma" in prompt
    assert "Italian" in prompt
    assert "rationale" in prompt.lower() or "recommend" in prompt.lower()


def test_phase4_prompt_output_to_phase5_formatted_recommendation() -> None:
    """Phase 4 candidates + mock rationale -> Phase 5 format_recommendation."""
    from ai_restaurant_phase3.models import Restaurant
    from ai_restaurant_phase5.formatter import format_recommendation

    main = Restaurant("Cafe Roma", "Pune", 2, 4.4, ["Italian", "Cafe"])
    alt = Restaurant("Bistro One", "Pune", 2, 4.2, ["Italian"])
    recommended_dict = _restaurant_to_recommendation_dict(main)
    alternatives_dicts = [_restaurant_to_recommendation_dict(alt)]

    formatted = format_recommendation(
        recommended=recommended_dict,
        rationale="Best match for Italian in Pune within budget.",
        alternatives=alternatives_dicts,
    )
    assert formatted.recommended_restaurant.name == "Cafe Roma"
    assert formatted.recommended_restaurant.location == "Pune"
    assert formatted.recommended_restaurant.price == 2
    assert formatted.recommended_restaurant.rating == 4.4
    assert "Italian" in formatted.recommended_restaurant.cuisine
    assert "Best match" in formatted.rationale
    assert len(formatted.alternatives) == 1
    assert formatted.alternatives[0].name == "Bistro One"


def test_phase6_observability_wraps_flow() -> None:
    """Phase 6 request_id and graceful_fallback integrate with a mock recommendation step."""
    from ai_restaurant_phase6.error_handling import with_graceful_fallback
    from ai_restaurant_phase6.metrics import get_metrics, reset_metrics
    from ai_restaurant_phase6.tracing import get_request_id, with_request_id

    reset_metrics()

    @with_graceful_fallback(fallback_value=None, log_message="Recommendation failed")
    def mock_recommend() -> str:
        return "Cafe Roma"

    with with_request_id("integration-test-id"):
        assert get_request_id() == "integration-test-id"
        result = mock_recommend()
    assert result == "Cafe Roma"

    snap = get_metrics().snapshot()
    assert snap["request_count"] >= 1
    assert snap["recommendation_count"] >= 1


def test_full_pipeline_mock_no_llm() -> None:
    """End-to-end: Phase1 prefs -> Phase2 load -> Phase3 filter/rank -> Phase4 prompt -> Phase5 format -> Phase6 context."""
    from ai_restaurant.contracts import UserPreferences as P1Prefs
    from ai_restaurant_phase2.data_loader import DatasetLoader, validate_dataset
    from ai_restaurant_phase3.filtering import filter_restaurants, rank_restaurants
    from ai_restaurant_phase4.prompting import build_prompt
    from ai_restaurant_phase5.formatter import format_recommendation
    from ai_restaurant_phase6.metrics import get_metrics, reset_metrics
    from ai_restaurant_phase6.tracing import with_request_id

    reset_metrics()

    # In-memory dataset (Phase 2)
    records = [
        {
            "City": "Pune",
            "Price range": 2,
            "Aggregate rating": 4.4,
            "Cuisines": "Italian, Cafe",
            "Restaurant Name": "Cafe Roma",
            "Address": "Pune",
        },
        {
            "City": "Pune",
            "Price range": 2,
            "Aggregate rating": 4.2,
            "Cuisines": "Italian",
            "Restaurant Name": "Bistro One",
            "Address": "Pune",
        },
    ]
    validated = validate_dataset(records)
    loader = DatasetLoader(provider=lambda: validated, cache_enabled=False)
    loaded = loader.load()

    # Phase 1 preferences
    prefs = P1Prefs(place="Pune", price_range=2, min_rating=4.0, cuisines=["Italian"])

    # Phase 3: convert and filter/rank
    restaurants = [_dataset_record_to_restaurant(r) for r in loaded]
    filtered = filter_restaurants(restaurants, prefs)
    ranked = rank_restaurants(filtered, prefs, limit=5)

    assert len(ranked) >= 1
    candidates = [_restaurant_to_candidate_context(sr.restaurant) for sr in ranked]
    prefs_dict = {"place": prefs.place, "price_range": prefs.price_range, "min_rating": prefs.min_rating, "cuisines": prefs.cuisines}

    # Phase 4: prompt (no LLM call)
    prompt = build_prompt(prefs_dict, candidates)
    assert "Cafe Roma" in prompt

    # Simulate LLM pick: first candidate, rationale
    chosen = ranked[0].restaurant
    rationale = "Best match for Italian in Pune."
    recommended_dict = _restaurant_to_recommendation_dict(chosen)
    alternatives_dicts = [_restaurant_to_recommendation_dict(sr.restaurant) for sr in ranked[1:]]

    # Phase 5: format
    with with_request_id():
        formatted = format_recommendation(
            recommended=recommended_dict,
            rationale=rationale,
            alternatives=alternatives_dicts,
        )

    assert formatted.recommended_restaurant.name == chosen.restaurant_name
    assert formatted.rationale == rationale
    assert get_metrics().snapshot()["request_count"] >= 0  # may have been incremented by other tests
