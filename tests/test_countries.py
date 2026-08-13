import pytest

from unsc.countries import UnknownCountry, to_iso3


@pytest.mark.parametrize(
    "name,code",
    [
        ("France", "FRA"),
        ("Russia", "RUS"),
        ("United Kingdom", "GBR"),
        ("Democratic Republic of the Congo", "COD"),
        ("Republic of Korea", "KOR"),
        ("Bahrain", "BHR"),
        ("Trinidad and Tobago", "TTO"),
    ],
)
def test_resolves_current_and_recent_members(name, code):
    assert to_iso3(name) == code


@pytest.mark.parametrize(
    "name,code",
    [
        ("Soviet Union", "SUN"),
        ("Yugoslavia", "YUG"),
        ("Czechoslovakia", "CSK"),
        ("Zaire", "COD"),
        ("Fourth Brazilian Republic", "BRA"),
        ("Ukrainian Soviet Socialist Republic", "UKR"),
    ],
)
def test_resolves_historical_states(name, code):
    assert to_iso3(name) == code


def test_ignores_the_arab_seat_star():
    assert to_iso3("Jordan*") == "JOR"


def test_unknown_names_raise_rather_than_guess():
    with pytest.raises(UnknownCountry, match="OVERRIDES"):
        to_iso3("Republic of Freedonia")


def test_near_miss_is_not_fuzzy_matched():
    # search_fuzzy() would happily return a country here. That is the failure
    # mode this module exists to prevent.
    with pytest.raises(UnknownCountry):
        to_iso3("Northern Ireland Republic of Nowhere")
