"""The guards are the only thing standing between a Wikipedia restructure and
a silently wrong payload, so each one gets an explicit test."""

import pytest

from unsc import guards
from unsc.countries import UnknownCountry
from unsc.membership import Member, parse_current

DROP_SOMALIA = ("|{{flagwrap|Somalia}}\n|[[African Group]]\n|2025\n|2026\n|-\n", "")
RENAME_FRANCE = ("{{flagwrap|France}}", "{{flagwrap|Freedonia}}")
DEMOTE_FRANCE = ("|{{flagwrap|France}}", "|{{flagwrap|Brazil}}")


def test_short_council_fails(article):
    mangled = article.replacing(*DROP_SOMALIA)
    assert mangled != article, "fixture drifted; update DROP_SOMALIA"
    with pytest.raises(guards.GuardFailed, match="expected 15 members, parsed 14"):
        guards.check_current(parse_current(mangled))


def test_wrong_permanent_members_fail(article):
    mangled = article.replacing(*DEMOTE_FRANCE, 1)
    with pytest.raises(guards.GuardFailed, match="permanent members"):
        guards.check_current(parse_current(mangled))


def test_unresolvable_name_fails_before_any_guard(article):
    with pytest.raises(UnknownCountry):
        parse_current(article.replacing(*RENAME_FRANCE))


def test_missing_section_fails(article):
    with pytest.raises(KeyError, match="Current membership"):
        parse_current(article.replacing("== Current membership ==", "== Members =="))


def test_partial_incoming_slate_fails():
    three = [Member(name=f"C{i}", iso3=f"X{i:02}", permanent=False) for i in range(3)]
    with pytest.raises(guards.GuardFailed, match="expected 0 or 5 incoming"):
        guards.check_incoming(three, 2026)


def test_update_writes_nothing_when_a_guard_fails(article, tmp_path, monkeypatch):
    import update
    from unsc import output
    from unsc.wiki import Article

    monkeypatch.setattr(output, "DOCS", tmp_path)
    monkeypatch.setattr(
        Article, "fetch", classmethod(lambda cls, *a, **k: article.replacing(*DROP_SOMALIA))
    )
    assert update.main() == 1
    assert list(tmp_path.iterdir()) == []
