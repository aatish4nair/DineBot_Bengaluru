from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    dataset_id: str = "ManikaSaini/zomato-restaurant-recommendation"
    cache_enabled: bool = True
