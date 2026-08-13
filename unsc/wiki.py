"""The source article, and pulling country names out of its table cells."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, replace

import mwparserfromhell
import requests

from .config import load_env
from .wikitable import Table

PAGE = "List of members of the United Nations Security Council"
API = "https://en.wikipedia.org/w/api.php"

# Wikimedia blocks clients that do not identify themselves, and there is no
# safe default: a made-up URL is what gets a client rate-limited.
USER_AGENT_ENV = "UNSC_API_USER_AGENT"

FLAG_TEMPLATES = {"flagwrap", "flag country", "flagcountry", "flag deco", "flag", "flagu"}
NOISE_TEMPLATES = {"efn", "notelist", "cite web", "cite book", "cite thesis", "sfn"}

HEADING_RE = re.compile(r"^(=+)([^=\n]+)\1\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Article:
    wikitext: str
    revid: int

    @classmethod
    def fetch(
        cls, page: str = PAGE, session: requests.Session | None = None
    ) -> Article:
        http = session or requests.Session()
        response = http.get(
            API,
            params={
                "action": "query",
                "prop": "revisions",
                "rvprop": "content|ids",
                "rvslots": "main",
                "format": "json",
                "formatversion": "2",
                "titles": page,
            },
            headers={"User-Agent": user_agent()},
            timeout=30,
        )
        response.raise_for_status()
        pages = response.json()["query"]["pages"]
        if not pages or pages[0].get("missing"):
            raise RuntimeError(f"Wikipedia page not found: {page}")
        revision = pages[0]["revisions"][0]
        return cls(
            wikitext=revision["slots"]["main"]["content"],
            revid=int(revision["revid"]),
        )

    def replacing(self, old: str, new: str, count: int = -1) -> Article:
        """A copy with a wikitext substitution applied, for tests and fixtures."""
        return replace(self, wikitext=self.wikitext.replace(old, new, count))

    def section(self, heading: str) -> str:
        """Return the body of the section with the given heading."""
        wanted = _normalise_heading(heading)
        for match in HEADING_RE.finditer(self.wikitext):
            if _normalise_heading(match.group(2)) != wanted:
                continue
            level = len(match.group(1))
            rest = self.wikitext[match.end() :]
            following = re.search(rf"^={{1,{level}}}[^=].*=+\s*$", rest, re.MULTILINE)
            return rest[: following.start()] if following else rest
        raise KeyError(f"section not found: {heading!r}")

    def table(self, heading: str) -> Table:
        return Table.parse(self.section(heading))

    def tables(self, heading: str) -> list[Table]:
        return Table.parse_all(self.section(heading))


def user_agent() -> str:
    load_env()
    value = os.environ.get(USER_AGENT_ENV, "").strip()
    if not value:
        raise RuntimeError(
            f"{USER_AGENT_ENV} is not set. Wikimedia requires a User-Agent naming "
            "the tool and a contact address, e.g. "
            f'{USER_AGENT_ENV}="unsc-api/1.0 (https://github.com/you/unsc-api; you@example.com)"'
        )
    return value


def _normalise_heading(text: str) -> str:
    """Casefold and unify dash variants — the article mixes - and –."""
    return re.sub(r"[‐-―]", "-", text).strip().casefold()


def _drop_disambiguator(title: str) -> str:
    """`Mauritius (1968–1992)` -> `Mauritius`."""
    return title.partition(" (")[0].strip() or title


def country_name(cell: str) -> str:
    """Extract a country name from a table cell.

    A wikilink's display text is the most reliable name when present, since it
    is what the article renders; otherwise fall back to the flag template's
    first argument.
    """
    code = mwparserfromhell.parse(cell)

    for tag in code.filter_tags(matches=lambda t: t.tag in ("ref", "sup")):
        code.remove(tag)
    for template in code.filter_templates():
        if template.name.strip().casefold() in NOISE_TEMPLATES:
            code.remove(template)

    for link in code.filter_wikilinks():
        if link.text:
            return str(link.text).strip()
        if title := str(link.title).strip():
            return _drop_disambiguator(title)

    for template in code.filter_templates():
        if template.name.strip().casefold() in FLAG_TEMPLATES and template.params:
            return _drop_disambiguator(str(template.params[0].value).strip())

    plain = code.strip_code().strip()
    if plain:
        return plain
    raise ValueError(f"no country name in cell: {cell!r}")


def is_empty_cell(cell: str) -> bool:
    return not cell.strip().strip("|—–- ?")
