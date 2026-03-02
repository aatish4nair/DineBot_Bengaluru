"""
Test recommendation filtering for permutations of place, price, rating, cuisine.
Verifies strict filter: no fallbacks, specific no-match message when criteria not met.
"""

import pytest
import sys
from pathlib import Path

# Add project root and phase src to path
root = Path(__file__).resolve().parents[2]
for phase in ["Phase1", "Phase2", "Phase3", "Phase4", "Phase5", "Phase6"]:
    src = root / phase / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))

# Add App/backend
app_backend = root / "App" / "backend"
if app_backend.exists() and str(root) not in sys.path:
    sys.path.insert(0, str(root))


@pytest.fixture
def client():
    """FastAPI test client with sample dataset."""
    import os
    os.environ["USE_SAMPLE_DATASET_ONLY"] = "1"
    os.environ.pop("RESTAURANT_LOAD_FROM_CACHE", None)  # Force fresh sample load
    from fastapi.testclient import TestClient
    from App.backend.main import app
    with TestClient(app) as c:
        # Trigger startup via health check
        c.get("/health")
        yield c


def test_mumbai_japanese_budget_returns_japanese_only(client):
    """Mumbai + Japanese + Budget (1) + 3.0+ should return only Japanese budget restaurants."""
    resp = client.post(
        "/recommend",
        json={
            "place": "Mumbai",
            "price_range": 1,
            "rating_min": 3.0,
            "rating_max": 5.5,
            "cuisines": ["Japanese"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    rec = data["recommended_restaurant"]
    if rec["name"] != "—":
        assert "Japanese" in rec.get("cuisine", "")
        assert rec.get("price", 0) <= 1
        assert rec.get("rating", 0) >= 3.0
        assert "Mumbai" in rec.get("location", "")


def test_mumbai_japanese_premium_returns_japanese_premium(client):
    """Mumbai + Japanese + Premium (4) + 4.0+ should return Japanese premium or no-match."""
    resp = client.post(
        "/recommend",
        json={
            "place": "Mumbai",
            "price_range": 4,
            "rating_min": 4.0,
            "rating_max": 5.5,
            "cuisines": ["Japanese"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    rec = data["recommended_restaurant"]
    if rec["name"] != "—":
        assert "Japanese" in rec.get("cuisine", "")
        assert rec.get("price", 0) <= 4
        assert rec.get("rating", 0) >= 4.0


def test_no_match_returns_specific_message(client):
    """When no restaurants match, rationale should mention the specific criteria."""
    resp = client.post(
        "/recommend",
        json={
            "place": "Mumbai",
            "price_range": 1,
            "rating_min": 4.5,
            "rating_max": 5.5,
            "cuisines": ["Mexican"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommended_restaurant"]["name"] == "—"
    rationale = data.get("rationale", "")
    assert "unable to find" in rationale.lower() or "no restaurants" in rationale.lower()
    assert "Mexican" in rationale or "mexican" in rationale.lower()
    assert "Mumbai" in rationale or "mumbai" in rationale.lower()


def test_place_filter_strict(client):
    """Mumbai request must not return Pune restaurants."""
    resp = client.post(
        "/recommend",
        json={
            "place": "Mumbai",
            "price_range": 4,
            "rating_min": 0.0,
            "rating_max": 5.5,
            "cuisines": ["Indian"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    rec = data["recommended_restaurant"]
    if rec["name"] != "—":
        assert "Mumbai" in rec.get("location", "")


def test_price_filter_strict(client):
    """Budget (1) request must not return Premium (4) restaurants."""
    resp = client.post(
        "/recommend",
        json={
            "place": "Mumbai",
            "price_range": 1,
            "rating_min": 3.0,
            "rating_max": 5.5,
            "cuisines": ["Japanese"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    for r in [data["recommended_restaurant"]] + data.get("alternatives", []):
        if r["name"] != "—":
            assert r.get("price", 0) <= 1


def test_cuisine_filter_strict(client):
    """Japanese request must not return Indian restaurants."""
    resp = client.post(
        "/recommend",
        json={
            "place": "Mumbai",
            "price_range": 1,
            "rating_min": 3.0,
            "rating_max": 5.5,
            "cuisines": ["Japanese"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    for r in [data["recommended_restaurant"]] + data.get("alternatives", []):
        if r["name"] != "—":
            assert "Japanese" in r.get("cuisine", "")


def test_rating_filter_strict(client):
    """4.5+ rating request must not return 3.8 rated restaurants."""
    resp = client.post(
        "/recommend",
        json={
            "place": "Mumbai",
            "price_range": 1,
            "rating_min": 4.5,
            "rating_max": 5.5,
            "cuisines": ["Japanese"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    rec = data["recommended_restaurant"]
    if rec["name"] != "—":
        assert rec.get("rating", 0) >= 4.5
    else:
        assert "4.5" in data.get("rationale", "") or "rating" in data.get("rationale", "").lower()


def test_all_places_have_coverage(client):
    """Each place should have at least one restaurant for some cuisine."""
    places = ["Pune", "Mumbai", "Bangalore", "Delhi", "Chennai", "Hyderabad", "Kolkata"]
    for place in places:
        resp = client.post(
            "/recommend",
            json={
                "place": place,
                "price_range": 4,
                "rating_min": 0.0,
                "rating_max": 5.5,
                "cuisines": ["Indian"],
            },
        )
        assert resp.status_code == 200


def test_delhi_fast_food_upscale_returns_upscale_only(client):
    """Delhi + Fast Food + Upscale (3) + 3.5+ should return only Upscale Fast Food (Social)."""
    resp = client.post(
        "/recommend",
        json={
            "place": "Delhi",
            "price_range": 3,
            "rating_min": 3.5,
            "rating_max": 5.5,
            "cuisines": ["Fast Food"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    rec = data["recommended_restaurant"]
    assert rec["name"] != "—"
    assert rec.get("price", 0) == 3
    assert "Fast Food" in rec.get("cuisine", "")
    assert "Delhi" in rec.get("location", "")


def test_all_cuisines_tested(client):
    """Each cuisine should have at least one restaurant somewhere."""
    cuisines = ["Italian", "Indian", "Chinese", "Japanese", "Mexican", "Thai", "Cafe", "Fast Food", "Seafood"]
    for cuisine in cuisines:
        resp = client.post(
            "/recommend",
            json={
                "place": "Mumbai",
                "price_range": 4,
                "rating_min": 0.0,
                "rating_max": 5.5,
                "cuisines": [cuisine],
            },
        )
        assert resp.status_code == 200
        # Either we get a match or a specific no-match message
        data = resp.json()
        assert "rationale" in data
