import os

from phase7_ui.config import UIConfig


def test_config_from_env_defaults(monkeypatch) -> None:
    monkeypatch.delenv("RECOMMENDER_API_BASE_URL", raising=False)
    monkeypatch.delenv("RECOMMENDER_API_RECOMMEND_PATH", raising=False)
    monkeypatch.delenv("RECOMMENDER_API_TIMEOUT_S", raising=False)

    cfg = UIConfig.from_env()
    assert cfg.api_base_url == "http://127.0.0.1:8000"
    assert cfg.recommend_path == "/recommend"
    assert cfg.request_timeout_s == 15.0


def test_config_from_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("RECOMMENDER_API_BASE_URL", "http://localhost:9999")
    monkeypatch.setenv("RECOMMENDER_API_RECOMMEND_PATH", "/v1/recommend")
    monkeypatch.setenv("RECOMMENDER_API_TIMEOUT_S", "3.5")

    cfg = UIConfig.from_env()
    assert cfg.api_base_url == "http://localhost:9999"
    assert cfg.recommend_path == "/v1/recommend"
    assert cfg.request_timeout_s == 3.5

