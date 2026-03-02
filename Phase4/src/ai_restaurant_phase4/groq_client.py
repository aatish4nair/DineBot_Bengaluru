from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GroqConfig:
    api_key_env: str = "GROQ_API_KEY"
    model: str = "llama3-70b-8192"


class GroqClient:
    def __init__(self, config: GroqConfig | None = None) -> None:
        self._config = config or GroqConfig()

    def _get_api_key(self) -> str:
        api_key = os.getenv(self._config.api_key_env)
        if not api_key:
            raise RuntimeError(
                "Groq API key not configured. Set GROQ_API_KEY to enable LLM calls."
            )
        return api_key

    def generate(self, prompt: str) -> str:
        _ = self._get_api_key()
        raise NotImplementedError(
            "Groq API integration pending. Provide API key to enable requests."
        )
