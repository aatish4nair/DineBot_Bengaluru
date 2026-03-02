from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .schema import DATASET_FIELD_MAPPING, REQUIRED_FIELDS

DatasetProvider = Callable[[], list[dict]]


def _is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def validate_dataset(
    records: Iterable[dict], mapping: dict[str, str] | None = None
) -> list[dict]:
    mapped = mapping or DATASET_FIELD_MAPPING
    normalized_records = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"record {index} is not a dict")
        translated = {internal: record.get(dataset) for internal, dataset in mapped.items()}
        missing = [key for key in REQUIRED_FIELDS if _is_blank(translated.get(key))]
        if missing:
            raise ValueError(f"record {index} missing fields: {', '.join(sorted(missing))}")

        price_range = translated["price_range"]
        if not isinstance(price_range, int) or not 1 <= price_range <= 4:
            raise ValueError(f"record {index} has invalid price_range")

        rating = translated["rating"]
        if not isinstance(rating, (int, float)) or not 0 <= float(rating) <= 5:
            raise ValueError(f"record {index} has invalid rating")

        cuisines = translated["cuisines"]
        if _is_blank(cuisines):
            raise ValueError(f"record {index} has invalid cuisines")

        normalized_records.append(record)

    if not normalized_records:
        raise ValueError("dataset is empty")

    return normalized_records


@dataclass
class DatasetLoader:
    provider: DatasetProvider
    cache_enabled: bool = True
    _cache: list[dict] | None = field(default=None, init=False, repr=False)

    def load(self) -> list[dict]:
        if self.cache_enabled and self._cache is not None:
            return list(self._cache)

        records = self.provider()
        validated = validate_dataset(records)
        if self.cache_enabled:
            self._cache = list(validated)
        return list(validated)
