from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    dataset_id: str = "ManikaSaini/zomato-restaurant-recommendation"
    llm_provider: str = "grok"
    cache_enabled: bool = True
