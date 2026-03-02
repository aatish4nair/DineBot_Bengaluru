import pytest

from ai_restaurant.contracts import (
    DATASET_FIELD_MAPPING,
    UserPreferences,
)


def test_user_preferences_accepts_valid_input() -> None:
    prefs = UserPreferences(
        place="Bangalore",
        price_range=2,
        min_rating=3.5,
        cuisines=["Italian", "Indian"],
    )
    assert prefs.place == "Bangalore"
    assert prefs.price_range == 2
    assert prefs.min_rating == 3.5
    assert prefs.cuisines == ["Italian", "Indian"]


@pytest.mark.parametrize(
    ("place", "price_range", "min_rating", "cuisines"),
    [
        ("", 2, 3.0, ["Thai"]),
        ("  ", 2, 3.0, ["Thai"]),
        ("Delhi", 0, 3.0, ["Thai"]),
        ("Delhi", 5, 3.0, ["Thai"]),
        ("Delhi", 2, -1.0, ["Thai"]),
        ("Delhi", 2, 6.0, ["Thai"]),
        ("Delhi", 2, 3.0, []),
        ("Delhi", 2, 3.0, [""]),
    ],
)
def test_user_preferences_validation_errors(
    place: str, price_range: int, min_rating: float, cuisines: list[str]
) -> None:
    with pytest.raises(ValueError):
        UserPreferences(
            place=place,
            price_range=price_range,
            min_rating=min_rating,
            cuisines=cuisines,
        )


def test_dataset_field_mapping_contains_expected_keys() -> None:
    for key in ["place", "price_range", "rating", "cuisines", "restaurant_name", "address"]:
        assert key in DATASET_FIELD_MAPPING
