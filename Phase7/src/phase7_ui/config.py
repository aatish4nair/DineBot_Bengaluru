from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _load_phase7_env() -> None:
    phase7_root = Path(__file__).resolve().parents[2]
    env_path = phase7_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)


@dataclass(frozen=True)
class UIConfig:
    api_base_url: str = "http://127.0.0.1:8000"
    recommend_path: str = "/recommend"
    request_timeout_s: float = 15.0

    @staticmethod
    def from_env() -> "UIConfig":
        _load_phase7_env()
        return UIConfig(
            api_base_url=os.getenv("RECOMMENDER_API_BASE_URL", "http://127.0.0.1:8000"),
            recommend_path=os.getenv("RECOMMENDER_API_RECOMMEND_PATH", "/recommend"),
            request_timeout_s=float(os.getenv("RECOMMENDER_API_TIMEOUT_S", "15.0")),
        )
