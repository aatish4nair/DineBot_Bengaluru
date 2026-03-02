import pytest

from ai_restaurant.api import recommend
from ai_restaurant.contracts import UserPreferences


def test_recommend_api_boundary_not_implemented() -> None:
    prefs = UserPreferences(
        place="Mumbai",
        price_range=3,
        min_rating=4.0,
        cuisines=["Mexican"],
    )
    with pytest.raises(NotImplementedError):
        recommend(prefs)
