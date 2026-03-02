from dataclasses import dataclass

from .groq_client import GroqClient
from .prompting import CandidateContext, build_prompt


@dataclass(frozen=True)
class OrchestrationResult:
    prompt: str
    response_text: str


class LLMOrchestrator:
    def __init__(self, client: GroqClient | None = None) -> None:
        self._client = client or GroqClient()

    def generate_recommendation(
        self, preferences: dict[str, object], candidates: list[CandidateContext]
    ) -> OrchestrationResult:
        prompt = build_prompt(preferences, candidates)
        response_text = self._client.generate(prompt)
        return OrchestrationResult(prompt=prompt, response_text=response_text)
