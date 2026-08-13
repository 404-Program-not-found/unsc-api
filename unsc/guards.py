"""Correctness gates. A failure aborts the run without writing anything.

Stateless checks, so they stay functions: a class here would hold nothing.
"""

from __future__ import annotations

from collections.abc import Sequence

from .membership import P5, Member

SEATS = 15
INCOMING_SEATS = 5


class GuardFailed(Exception):
    pass


def check_current(members: Sequence[Member]) -> None:
    if len(members) != SEATS:
        raise GuardFailed(
            f"expected {SEATS} members, parsed {len(members)}: "
            + ", ".join(m.name for m in members)
        )

    permanent = {m.iso3 for m in members if m.permanent}
    if permanent != P5:
        raise GuardFailed(
            f"permanent members are {sorted(permanent)}, expected {sorted(P5)}"
        )

    codes = [m.iso3 for m in members]
    if len(set(codes)) != len(codes):
        raise GuardFailed(f"duplicate members: {sorted(codes)}")


def check_incoming(incoming: Sequence[Member], year: int) -> None:
    """Incoming is empty before the June election, then exactly five."""
    if incoming and len(incoming) != INCOMING_SEATS:
        raise GuardFailed(
            f"expected 0 or {INCOMING_SEATS} incoming members for {year + 1}, "
            f"got {len(incoming)}: " + ", ".join(m.name for m in incoming)
        )
