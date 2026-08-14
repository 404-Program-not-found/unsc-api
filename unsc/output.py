"""Writing the published JSON payloads."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .membership import Member

SCHEMA_VERSION = 1
DOCS = Path(__file__).resolve().parent.parent / "docs"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class Source:
    page: str
    revid: int


@dataclass(frozen=True)
class Payload:
    """One published file: a membership list plus its provenance."""

    members: Sequence[Member]
    year: int
    source: Source
    generated_at: str

    def as_json(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": self.generated_at,
            "source": {"page": self.source.page, "revid": self.source.revid},
            "year": self.year,
            "members": [m.as_json() for m in self.members],
        }


class Publisher:
    """Writes payloads under `docs/`, which GitHub Pages serves verbatim.

    Year payloads carry no `.json` suffix, so the published paths are
    `/incoming` and `/years/2026`. Pages then serves them as
    `application/octet-stream`, and Cloudflare rewrites the header at the edge.
    The two `index.json` files keep theirs — a bare `index` collides with
    directory-index resolution — and Pages types them correctly on its own.
    """

    def __init__(self, root: Path | None = None) -> None:
        # Resolved at call time so tests can redirect DOCS to a tmp_path.
        self.root = root if root is not None else DOCS

    def write(self, relative: str, data: dict[str, Any]) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        path.write_text(text, encoding="utf-8")
        return path

    def write_payload(self, relative: str, payload: Payload) -> Path:
        return self.write(relative, payload.as_json())

    def write_index(self, **extra: Any) -> Path:
        # Filtered on isdigit rather than globbed: the directory also holds
        # this manifest, and `index.json` does not survive an int().
        years = sorted(
            int(p.name) for p in (self.root / "years").iterdir() if p.name.isdigit()
        )
        index = {"schema_version": SCHEMA_VERSION, "years": years, **extra}
        return self.write("years/index.json", index)
