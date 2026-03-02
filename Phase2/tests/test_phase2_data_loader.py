import pytest

from ai_restaurant_phase2.data_loader import DatasetLoader, validate_dataset


def _sample_record(overrides: dict | None = None) -> dict:
    base = {
        "City": "Pune",
        "Price range": 2,
        "Aggregate rating": 4.2,
        "Cuisines": "Italian",
        "Restaurant Name": "Cafe Roma",
        "Address": "Central Pune",
    }
    if overrides:
        base.update(overrides)
    return base


def test_validate_dataset_accepts_valid_records() -> None:
    records = [_sample_record(), _sample_record({"Restaurant Name": "Cafe Uno"})]
    assert validate_dataset(records) == records


@pytest.mark.parametrize(
    ("overrides", "error_message"),
    [
        ({"City": ""}, "missing fields"),
        ({"Price range": 0}, "invalid price_range"),
        ({"Price range": 5}, "invalid price_range"),
        ({"Aggregate rating": -1}, "invalid rating"),
        ({"Aggregate rating": 6}, "invalid rating"),
        ({"Cuisines": ""}, "missing fields"),
    ],
)
def test_validate_dataset_rejects_invalid_records(
    overrides: dict, error_message: str
) -> None:
    with pytest.raises(ValueError) as excinfo:
        validate_dataset([_sample_record(overrides)])
    assert error_message in str(excinfo.value)


def test_validate_dataset_rejects_empty_dataset() -> None:
    with pytest.raises(ValueError, match="dataset is empty"):
        validate_dataset([])


def test_loader_caches_when_enabled() -> None:
    calls = {"count": 0}

    def provider() -> list[dict]:
        calls["count"] += 1
        return [_sample_record()]

    loader = DatasetLoader(provider=provider, cache_enabled=True)
    first = loader.load()
    second = loader.load()

    assert calls["count"] == 1
    assert first == second


def test_loader_does_not_cache_when_disabled() -> None:
    calls = {"count": 0}

    def provider() -> list[dict]:
        calls["count"] += 1
        return [_sample_record({"Restaurant Name": f"Cafe {calls['count']}"})]

    loader = DatasetLoader(provider=provider, cache_enabled=False)
    first = loader.load()
    second = loader.load()

    assert calls["count"] == 2
    assert first != second
