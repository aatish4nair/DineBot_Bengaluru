from __future__ import annotations

import json
from dataclasses import dataclass

import requests

from .config import UIConfig
from .models import PreferenceInput, RecommendationView


class ApiError(RuntimeError):
    pass


@dataclass
class ApiClient:
    config: UIConfig

    def recommend(self, prefs: PreferenceInput) -> RecommendationView:
        url = self.config.api_base_url.rstrip("/") + self.config.recommend_path
        try:
            resp = requests.post(
                url,
                json=prefs.to_payload(),
                timeout=self.config.request_timeout_s,
            )
        except requests.RequestException as e:
            raise ApiError(f"Failed to connect to API at {url}: {e}") from e

        if resp.status_code >= 400:
            raise ApiError(f"API returned {resp.status_code}: {resp.text[:500]}")

        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            raise ApiError("API response was not valid JSON") from e

        if not isinstance(data, dict):
            raise ApiError("API response JSON must be an object")

        view = RecommendationView.from_dict(data)
        if not view.rationale:
            raise ApiError("API response missing required field: rationale")
        return view
