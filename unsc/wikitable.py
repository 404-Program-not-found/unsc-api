"""Wikitext tables as objects: a `Table` of `Row`s of `Cell`s.

The membership tables use `rowspan` for two-year terms, so a row's raw cells do
not line up with its columns. `Table.parse` expands spans into a dense grid
where every position holds the cell covering it.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

ROWSPAN_RE = re.compile(r"\browspan\s*=\s*\"?(\d+)", re.IGNORECASE)
COLSPAN_RE = re.compile(r"\bcolspan\s*=\s*\"?(\d+)", re.IGNORECASE)
# A cell prefix is attributes only if it carries an attr= and no wiki markup.
ATTR_RE = re.compile(r"^[^|\[\]{}]*=[^|\[\]{}]*$")


@dataclass(frozen=True)
class Cell:
    text: str
    rowspan: int = 1
    colspan: int = 1
    header: bool = False


@dataclass(frozen=True)
class Row:
    cells: list[Cell]

    @property
    def texts(self) -> list[str]:
        return [cell.text for cell in self.cells]

    def __iter__(self) -> Iterator[Cell]:
        return iter(self.cells)

    def __len__(self) -> int:
        return len(self.cells)

    def __getitem__(self, index):
        return self.cells[index]


@dataclass(frozen=True)
class Table:
    rows: list[Row]

    @classmethod
    def parse(cls, wikitext: str) -> Table:
        """Parse the first `{| ... |}` block in `wikitext`."""
        source = next(cls.sources(wikitext), None)
        if source is None:
            raise ValueError("no wikitable found")
        return cls._from_source(source)

    @classmethod
    def parse_all(cls, wikitext: str) -> list[Table]:
        return [cls._from_source(source) for source in cls.sources(wikitext)]

    @staticmethod
    def sources(wikitext: str) -> Iterator[str]:
        """Yield each top-level `{| ... |}` block, nested tables kept intact."""
        position = 0
        while (start := wikitext.find("{|", position)) != -1:
            depth = 0
            for match in re.finditer(r"\{\||\|\}", wikitext[start:]):
                depth += 1 if match.group() == "{|" else -1
                if depth == 0:
                    end = start + match.end()
                    yield wikitext[start:end]
                    position = end
                    break
            else:
                return

    @classmethod
    def _from_source(cls, source: str) -> Table:
        return cls(rows=_expand_spans(_raw_rows(source)))

    @property
    def header(self) -> Row:
        return self.rows[0]

    @property
    def body(self) -> list[Row]:
        return self.rows[1:]

    def column(self, index: int) -> list[Cell]:
        return [row[index] for row in self.rows if index < len(row)]


def split_top_level(text: str, sep: str) -> list[str]:
    """Split on `sep`, ignoring separators inside {{...}} or [[...]].

    Templates carry their own pipes (`{{flagwrap|Japan|1947}}`), so a naive
    split corrupts every cell containing one.
    """
    parts: list[str] = []
    buf: list[str] = []
    depth = i = 0
    while i < len(text):
        pair = text[i : i + 2]
        if pair in ("{{", "[["):
            depth += 1
            buf.append(pair)
            i += 2
            continue
        if pair in ("}}", "]]"):
            depth = max(0, depth - 1)
            buf.append(pair)
            i += 2
            continue
        if depth == 0 and text.startswith(sep, i):
            parts.append("".join(buf))
            buf = []
            i += len(sep)
            continue
        buf.append(text[i])
        i += 1
    parts.append("".join(buf))
    return parts


def _strip_attributes(cell: str) -> str:
    """Drop a leading `width="10%" rowspan="2" |` attribute block."""
    pieces = split_top_level(cell, "|")
    if len(pieces) > 1 and ATTR_RE.match(pieces[0].strip()):
        return "|".join(pieces[1:]).strip()
    return cell.strip()


def _parse_cells(line: str, header: bool) -> list[Cell]:
    # Header rows accept `!!` and `||` interchangeably; the article uses both.
    chunks = split_top_level(line, "||")
    if header:
        chunks = [part for chunk in chunks for part in split_top_level(chunk, "!!")]

    cells: list[Cell] = []
    for raw in chunks:
        attrs = split_top_level(raw, "|")[0]
        rowspan = ROWSPAN_RE.search(attrs)
        colspan = COLSPAN_RE.search(attrs)
        cells.append(
            Cell(
                text=_strip_attributes(raw),
                rowspan=int(rowspan.group(1)) if rowspan else 1,
                colspan=int(colspan.group(1)) if colspan else 1,
                header=header,
            )
        )
    return cells


def _raw_rows(source: str) -> list[list[Cell]]:
    """Split one table's wikitext into rows of unplaced cells."""
    rows: list[list[Cell]] = []
    current: list[Cell] | None = None
    for line in source.splitlines()[1:]:
        line = line.rstrip()
        if line.startswith("|-"):
            if current is not None:
                rows.append(current)
            current = []
            continue
        if line.startswith("|}"):
            break
        if not line or line[0] not in "|!":
            continue
        if current is None:
            current = []
        current.extend(_parse_cells(line[1:], header=line[0] == "!"))
    if current:
        rows.append(current)
    return rows


def _expand_spans(raw_rows: list[list[Cell]]) -> list[Row]:
    """Place cells into a grid, carrying rowspans down and colspans across.

    Each row maps column index -> cell. A cell claims every position its spans
    cover, so a position already claimed from above is simply skipped over.
    """
    grid: list[dict[int, Cell]] = [{} for _ in raw_rows]

    for r, cells in enumerate(raw_rows):
        col = 0
        for cell in cells:
            while col in grid[r]:
                col += 1
            for dr in range(cell.rowspan):
                for dc in range(cell.colspan):
                    if r + dr < len(grid):
                        grid[r + dr].setdefault(col + dc, cell)
            col += cell.colspan

    return [Row(cells=[row[col] for col in sorted(row)]) for row in grid]
