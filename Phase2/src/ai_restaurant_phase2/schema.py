DATASET_FIELD_MAPPING = {
    "place": "City",
    "price_range": "Price range",
    "rating": "Aggregate rating",
    "cuisines": "Cuisines",
    "restaurant_name": "Restaurant Name",
    "address": "Address",
}

REQUIRED_FIELDS = {
    "place",
    "price_range",
    "rating",
    "cuisines",
    "restaurant_name",
    "address",
}


def get_dataset_field_mapping() -> dict[str, str]:
    return dict(DATASET_FIELD_MAPPING)
