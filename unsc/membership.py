"""Council membership records, and the article tables they come from."""

from __future__ import annotations

import re
from collections.abc import Container, Iterator
from dataclasses import asdict, dataclass
from typing import Any

from . import wiki
from .countries import to_iso3
from .wiki import Article
from .wikitable import Table

P5 = frozenset({"CHN", "FRA", "RUS", "GBR", "USA"})

PERMANENT_HEADING = "Permanent"
ELECTED_HEADING = "Non-permanent (1966–present)"
EARLY_ELECTED_HEADING = "Non-permanent (1946–1965)"
CURRENT_HEADING = "Current membership"

YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")

GROUP_SLUGS = (
    ("african", "african"),
    ("asia", "asia_pacific"),
    ("latin american", "latin_american_caribbean"),
    ("western european", "western_european_others"),
    ("eastern european", "eastern_european"),
)


@dataclass(frozen=True)
class Member:
    name: str
    iso3: str
    permanent: bool
    regional_group: str | None = None
    term_start: int | None = None
    term_end: int | None = None

    @classmethod
    def from_cell(
        cls,
        cell: str,
        header: str = "",
        *,
        permanent: bool,
        term_start: int | None = None,
        term_end: int | None = None,
    ) -> Member:
        """Build a member from one country cell and its column header."""
        name = wiki.country_name(cell)
        return cls(
            name=name,
            iso3=to_iso3(name),
            permanent=permanent,
            regional_group=regional_group(header),
            term_start=term_start,
            term_end=term_end,
        )

    def as_json(self) -> dict[str, Any]:
        return asdict(self)


def regional_group(text: str) -> str | None:
    lowered = text.casefold()
    return next((slug for needle, slug in GROUP_SLUGS if needle in lowered), None)


def cell_year(text: str) -> int | None:
    """Pull a four-digit year out of a table cell, if it has one."""
    match = YEAR_RE.search(wiki.country_name(text))
    return int(match.group(1)) if match else None


@dataclass(frozen=True)
class SeatRow:
    """One year-keyed row: the year, its country cells, and their seat headers."""

    year: int
    cells: list[str]
    headers: list[str]

    def members(
        self,
        *,
        permanent: bool,
        term_start: int | None = None,
        term_end: int | None = None,
    ) -> list[Member]:
        """Every filled seat in the row. Empty cells are seats it does not fill."""
        return [
            Member.from_cell(
                cell,
                self.headers[index] if index < len(self.headers) else "",
                permanent=permanent,
                term_start=term_start,
                term_end=term_end,
            )
            for index, cell in enumerate(self.cells)
            if not wiki.is_empty_cell(cell)
        ]


class ByYearTable:
    """A table whose first column is a year and whose rest are seats.

    Every historical table in the article has this shape, so the permanent,
    early-elected and modern-elected tables all read through here.
    """

    def __init__(self, table: Table) -> None:
        self.table = table

    @classmethod
    def from_article(cls, article: Article, heading: str) -> ByYearTable:
        return cls(article.table(heading))

    def __iter__(self) -> Iterator[SeatRow]:
        headers = self.table.header.texts[1:]
        for row in self.table.body:
            cells = row.texts
            if len(cells) < 2:
                continue
            if (year := cell_year(cells[0])) is not None:
                yield SeatRow(year=year, cells=cells[1:], headers=headers)

    def row_for(self, year: int) -> SeatRow | None:
        return next((row for row in self if row.year == year), None)

    def members_by_year(self, *, permanent: bool) -> dict[int, list[Member]]:
        return {row.year: row.members(permanent=permanent) for row in self}


def parse_current(article: Article) -> list[Member]:
    """Parse the two flat tables under `== Current membership ==`.

    Unlike the by-year tables these are one country per row, with the term in
    its own columns.
    """
    tables = article.tables(CURRENT_HEADING)
    if len(tables) != 2:
        raise ValueError(
            f"expected permanent + non-permanent tables, got {len(tables)}"
        )

    members: list[Member] = []
    for table, permanent in zip(tables, (True, False), strict=True):
        for row in table.body:
            cells = row.texts
            if len(cells) < 2:
                continue
            members.append(
                Member.from_cell(
                    cells[0],
                    cells[1],
                    permanent=permanent,
                    term_start=None if permanent else cell_year(cells[2]),
                    term_end=None if permanent else cell_year(cells[3]),
                )
            )
    return members


def parse_incoming(
    article: Article, current_year: int, sitting: Container[str]
) -> list[Member]:
    """Members elected but not yet seated: next year's row, minus this year's.

    Empty for roughly half the year — the row only appears once the June
    election results are written up.
    """
    term_start = current_year + 1
    row = ByYearTable.from_article(article, ELECTED_HEADING).row_for(term_start)
    if row is None:
        return []

    elected = row.members(
        permanent=False, term_start=term_start, term_end=term_start + 1
    )
    return [m for m in elected if m.iso3 not in sitting]


def elected_by_year(article: Article, heading: str) -> dict[int, list[Member]]:
    return ByYearTable.from_article(article, heading).members_by_year(permanent=False)


def permanent_by_year(article: Article, through: int) -> dict[int, list[Member]]:
    """Forward-fill the sparse `=== Permanent ===` table.

    Its rows are keyed by the year a seat changed hands, not by every year, so
    each row states the composition from that year until the next row.
    """
    changes = ByYearTable.from_article(article, PERMANENT_HEADING).members_by_year(
        permanent=True
    )

    filled: dict[int, list[Member]] = {}
    current: list[Member] = []
    for year in range(min(changes), through + 1):
        current = changes.get(year, current)
        filled[year] = current
    return filled
