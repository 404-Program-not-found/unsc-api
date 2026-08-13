"""
Resolve Wikipedia country names to stable ISO 3166 alpha-3 codes.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from functools import cached_property

import country_converter  # type: ignore[import-untyped]
import pycountry

NOT_FOUND = "not found"

# Consulted before coco, which is variously wrong, silent, or right by luck on
# these. Grouped by which code is correct and why, since that is the only
# question an entry has to answer.
OVERRIDES: dict[str, str] = {
    # Dissolved states
    "czechoslovakia": "CSK",
    "czechoslovak socialist republic": "CSK",
    "yugoslavia": "YUG",
    "socialist federal republic of yugoslavia": "YUG",
    "federal people's republic of yugoslavia": "YUG",
    "east germany": "DDR",
    "german democratic republic": "DDR",
    # Constituent republics that sat in their own right
    "ukrainian soviet socialist republic": "UKR", # coco answers ['SUN', 'UKR']
    "byelorussian soviet socialist republic": "BLR",
    # Continuing states under an earlier name: the modern code is correct.
    "tanganyika": "TZA", # coco returns EAT for Tanganyika for some reason
    "united arab republic": "EGY",
    "spanish state": "ESP",
    "people's republic of the congo": "COG",
    # Regime-era article titles
    "french fourth republic": "FRA",
    "french fifth republic": "FRA",
    "hungarian people's republic": "HUN",
    "polish people's republic": "POL",
    "west germany": "DEU",
}


class UnknownCountry(Exception):
    """A name did not resolve."""


class CountryResolver:
    def __init__(self, overrides: Mapping[str, str] | None = None) -> None:
        self.overrides = dict(OVERRIDES if overrides is None else overrides)

    @cached_property
    def converter(self) -> country_converter.CountryConverter:
        logging.getLogger("country_converter").setLevel(logging.ERROR)
        return country_converter.CountryConverter(include_obsolete=True)

    @cached_property
    def valid_codes(self) -> frozenset[str]:
        """Every assignable ISO alpha-3, current (3166-1) or withdrawn (3166-3)."""
        current = {c.alpha_3 for c in pycountry.countries}
        withdrawn = {
            code
            for c in pycountry.historic_countries
            if (code := getattr(c, "alpha_3", None))
        }
        return frozenset(current | withdrawn)

    def resolve_all(self, names: Sequence[str]) -> list[str]:
        """Resolve a batch of names, raising on the first that does not resolve."""
        if not names:
            return []

        cleaned = [" ".join(n.split()).strip(" *") for n in names]
        unmatched = [n for n in cleaned if n.casefold() not in self.overrides]
        matched = (
            dict(zip(unmatched, self._convert(unmatched), strict=True))
            if unmatched
            else {}
        )
        return [
            self._checked(name, self.overrides.get(name.casefold(), "") or matched[name])
            for name in cleaned
        ]

    def to_iso3(self, name: str) -> str:
        return self.resolve_all([name])[0]

    def _checked(self, name: str, code: str) -> str:
        if code == NOT_FOUND:
            raise UnknownCountry(
                f"{name!r} did not resolve to an ISO code. If it is a historical "
                "state, add it to OVERRIDES in unsc/countries.py."
            )
        if code not in self.valid_codes:
            raise UnknownCountry(
                f"{name!r} resolved to {code!r}, which is not an ISO 3166 alpha-3 "
                "code. Add an explicit entry to OVERRIDES in unsc/countries.py."
            )
        return code

    def _convert(self, names: Sequence[str]) -> list[str]:
        codes = self.converter.convert(names, to="ISO3", not_found=NOT_FOUND)
        return [codes] if isinstance(codes, str) else list(codes)


RESOLVER = CountryResolver()


def to_iso3(name: str) -> str:
    """Return the ISO alpha-3 code for a country name, or raise."""
    return RESOLVER.to_iso3(name)


def valid_codes() -> frozenset[str]:
    return RESOLVER.valid_codes
