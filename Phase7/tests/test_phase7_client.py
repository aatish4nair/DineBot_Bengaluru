import json

import pytest

from phase7_ui.client import ApiClient, ApiError
from phase7_ui.config import UIConfig
from phase7_ui.models import PreferenceInput


class _Resp:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise json.JSONDecodeError("bad", "x", 0)
        return self._payload


def test_client_posts_correct_payload(monkeypatch) -> None:
    captured = {}

    def fake_post(url, json=None, timeout=None):  # noqa: A002
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _Resp(
            200,
            payload={
                "recommended_restaurant": {
                    "name": "Cafe Roma",
                    "location": "Pune",
                    "price": 2,
                    "rating": 4.4,
                    "cuisine": "Italian",
                },
                "rationale": "Good fit.",
                "alternatives": [],
            },
        )

    import phase7_ui.client as client_mod

    monkeypatch.setattr(client_mod.requests, "post", fake_post)

    cfg = UIConfig(api_base_url="http://localhost:8000", recommend_path="/recommend", request_timeout_s=2.0)
    client = ApiClient(cfg)
    prefs = PreferenceInput(place="Pune", price_range=2, rating_min=4.0, rating_max=5.5, cuisines=["Italian"])
    rec = client.recommend(prefs)

    assert captured["url"] == "http://localhost:8000/recommend"
    assert captured["timeout"] == 2.0
    assert captured["json"]["place"] == "Pune"
    assert rec.recommended_restaurant.name == "Cafe Roma"
    assert rec.rationale == "Good fit."


def test_client_raises_on_http_error(monkeypatch) -> None:
    def fake_post(url, json=None, timeout=None):  # noqa: A002
        return _Resp(500, payload={"error": "x"}, text="server error")

    import phase7_ui.client as client_mod

    monkeypatch.setattr(client_mod.requests, "post", fake_post)

    client = ApiClient(UIConfig())
    prefs = PreferenceInput(place="Pune", price_range=2, rating_min=4.0, rating_max=5.5, cuisines=["Italian"])
    with pytest.raises(ApiError, match="API returned 500"):
        client.recommend(prefs)


def test_client_raises_on_invalid_json(monkeypatch) -> None:
    def fake_post(url, json=None, timeout=None):  # noqa: A002
        return _Resp(200, payload=None, text="not json")

    import phase7_ui.client as client_mod

    monkeypatch.setattr(client_mod.requests, "post", fake_post)

    client = ApiClient(UIConfig())
    prefs = PreferenceInput(place="Pune", price_range=2, rating_min=4.0, rating_max=5.5, cuisines=["Italian"])
    with pytest.raises(ApiError, match="valid JSON"):
        client.recommend(prefs)


def test_client_raises_when_rationale_missing(monkeypatch) -> None:
    def fake_post(url, json=None, timeout=None):  # noqa: A002
        return _Resp(200, payload={"recommended_restaurant": {"name": "X"}}, text="")

    import phase7_ui.client as client_mod

    monkeypatch.setattr(client_mod.requests, "post", fake_post)

    client = ApiClient(UIConfig())
    prefs = PreferenceInput(place="Pune", price_range=2, rating_min=4.0, rating_max=5.5, cuisines=["Italian"])
    with pytest.raises(ApiError, match="rationale"):
        client.recommend(prefs)

