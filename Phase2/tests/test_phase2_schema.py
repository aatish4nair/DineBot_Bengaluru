from ai_restaurant_phase2.schema import DATASET_FIELD_MAPPING, REQUIRED_FIELDS


def test_dataset_field_mapping_contains_expected_keys() -> None:
    assert REQUIRED_FIELDS.issubset(DATASET_FIELD_MAPPING.keys())


def test_dataset_field_mapping_contains_expected_values() -> None:
    expected_values = {
        "City",
        "Price range",
        "Aggregate rating",
        "Cuisines",
        "Restaurant Name",
        "Address",
    }
    assert set(DATASET_FIELD_MAPPING.values()) == expected_values
