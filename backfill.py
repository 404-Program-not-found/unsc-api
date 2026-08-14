#!/usr/bin/env python3
"""One-shot: write `docs/years/YYYY.json` for every year back to 1946.

Run manually, review the diff, commit. Kept off the cron path so a formatting
quirk in a 1954 row can never break tomorrow's update.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from unsc.countries import UnknownCountry
from unsc.membership import (
    EARLY_ELECTED_HEADING,
    ELECTED_HEADING,
    Member,
    elected_by_year,
    permanent_by_year,
)
from unsc.output import Payload, Publisher, Source, now_iso
from unsc.wiki import PAGE, Article

FIRST_YEAR = 1946
EXPANSION_YEAR = 1966  # council grew from 11 seats to 15
SEATS_BEFORE_EXPANSION = 11
SEATS_AFTER_EXPANSION = 15


def check(year: int, members: Sequence[Member]) -> str | None:
    """Return why `year` is unpublishable, or None if it is fine."""
    expected = (
        SEATS_AFTER_EXPANSION if year >= EXPANSION_YEAR else SEATS_BEFORE_EXPANSION
    )
    if len(members) != expected:
        return f"{year}: expected {expected} seats, got {len(members)}"
    codes = [m.iso3 for m in members]
    if len(set(codes)) != len(codes):
        return f"{year}: duplicate members {sorted(codes)}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--through", type=int, help="last year to write")
    parser.add_argument(
        "--strict", action="store_true", help="abort instead of skipping bad years"
    )
    args = parser.parse_args()

    article = Article.fetch()
    modern = elected_by_year(article, ELECTED_HEADING)
    through = args.through or max(modern)

    permanent = permanent_by_year(article, through)
    elected = elected_by_year(article, EARLY_ELECTED_HEADING) | modern

    source = Source(page=PAGE, revid=article.revid)
    generated_at = now_iso()
    publisher = Publisher()

    written = 0
    problems: list[str] = []
    for year in range(FIRST_YEAR, through + 1):
        members = permanent.get(year, []) + elected.get(year, [])
        if problem := check(year, members):
            problems.append(problem)
            continue
        publisher.write_payload(
            f"years/{year}/index.json", Payload(members, year, source, generated_at)
        )
        written += 1

    publisher.write_index(generated_at=generated_at, current_year=through)

    for problem in problems:
        print(f"skipped {problem}", file=sys.stderr)
    print(f"wrote {written} years, skipped {len(problems)}")
    return 1 if problems and args.strict else 0


if __name__ == "__main__":
    try:
        status = main()
    except UnknownCountry as error:
        print(f"backfill aborted: {error}", file=sys.stderr)
        status = 1
    raise SystemExit(status)
