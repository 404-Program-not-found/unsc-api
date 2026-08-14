#!/usr/bin/env python3
"""Daily job: publish the current Security Council membership as static JSON.

Parses only the current year; anything historical is `backfill.py`'s problem.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from unsc import guards
from unsc.countries import UnknownCountry
from unsc.membership import parse_current, parse_incoming
from unsc.output import Payload, Publisher, Source, now_iso
from unsc.wiki import PAGE, Article


def main() -> int:
    year = datetime.now(timezone.utc).year
    article = Article.fetch()

    try:
        members = parse_current(article)
        guards.check_current(members)

        sitting = {m.iso3 for m in members}
        incoming = parse_incoming(article, year, sitting)
        guards.check_incoming(incoming, year)
    except (guards.GuardFailed, UnknownCountry, ValueError, KeyError) as error:
        print(f"refusing to write: {error}", file=sys.stderr)
        print(f"source revid: {article.revid}", file=sys.stderr)
        return 1

    source = Source(page=PAGE, revid=article.revid)
    generated_at = now_iso()
    publisher = Publisher()

    current = Payload(members, year, source, generated_at)
    publisher.write_payload("index.json", current)
    publisher.write_payload(f"years/{year}", current)
    publisher.write_payload(
        "incoming", Payload(incoming, year + 1, source, generated_at)
    )
    publisher.write_index(generated_at=generated_at, current_year=year)

    print(f"{len(members)} members, {len(incoming)} incoming, revid {article.revid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
