"""The hand-written overrides assert facts, so they get checked.

A typo like SUM for SUN would otherwise ship a plausible-looking code straight
into the published payload.
"""

import pytest

from unsc.countries import OVERRIDES, to_iso3, valid_codes


@pytest.mark.parametrize("name,code", sorted(OVERRIDES.items()))
def test_every_entry_is_a_real_iso_code(name, code):
    assert code in valid_codes(), f"{name} -> {code} is not an ISO 3166 alpha-3 code"


@pytest.mark.parametrize("name", sorted(OVERRIDES))
def test_keys_are_casefolded_so_lookups_hit(name):
    assert name == name.casefold()


def test_every_yugoslav_title_maps_to_the_same_dissolved_state():
    yugoslav = {n: c for n, c in OVERRIDES.items() if "yugoslav" in n}
    assert set(yugoslav.values()) == {"YUG"}, yugoslav


@pytest.mark.parametrize(
    "name,code",
    [
        ("Ukrainian SSR", "UKR"),
        ("Byelorussian SSR", "BLR"),
        ("Prov. Gov. of France", "FRA"),
        ("Federal Republic of Germany", "DEU"),
    ],
)
def test_names_left_to_coco_still_resolve(name, code):
    # These were dropped from OVERRIDES because coco already answers them
    # correctly. If its data ever changes, they need to come back.
    assert to_iso3(name) == code


@pytest.mark.parametrize(
    "name,code",
    [
        # Dissolved states keep their own code rather than a successor's.
        ("Czechoslovakia", "CSK"),
        ("Yugoslavia", "YUG"),
        ("East Germany", "DDR"),
        ("Union of Soviet Socialist Republics", "SUN"),
        # A constituent republic that held its own seat.
        ("Ukrainian Soviet Socialist Republic", "UKR"),
        # Continuing states under an earlier name.
        ("Tanganyika", "TZA"),
        ("Ceylon", "LKA"),
        ("Upper Volta", "BFA"),
        ("Zaire", "COD"),
        # Regime-era titles.
        ("Ba'athist Iraq", "IRQ"),
        ("Hungarian People's Republic", "HUN"),
        ("French Fourth Republic", "FRA"),
    ],
)
def test_historical_names_resolve_correctly(name, code):
    assert to_iso3(name) == code


def test_tanganyika_is_not_left_as_cocos_non_iso_code():
    # coco returns EAT here, which is three uppercase letters and would pass a
    # naive shape check while not being an ISO code at all.
    assert to_iso3("Tanganyika") == "TZA"
