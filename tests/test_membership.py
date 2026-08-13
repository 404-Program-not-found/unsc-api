import pytest

from unsc import guards
from unsc.membership import P5, parse_current, parse_incoming


@pytest.fixture(scope="module")
def members(article):
    return parse_current(article)


def test_parses_fifteen_members(members):
    assert len(members) == 15


def test_permanent_members_are_the_p5(members):
    assert {m.iso3 for m in members if m.permanent} == set(P5)


def test_elected_members_carry_their_term(members):
    bahrain = next(m for m in members if m.iso3 == "BHR")
    assert (bahrain.term_start, bahrain.term_end) == (2026, 2027)
    assert bahrain.permanent is False


def test_permanent_members_have_no_term(members):
    france = next(m for m in members if m.iso3 == "FRA")
    assert france.term_start is None and france.term_end is None


def test_regional_groups_are_slugged(members):
    somalia = next(m for m in members if m.iso3 == "SOM")
    assert somalia.regional_group == "african"


def test_incoming_is_the_five_newly_elected(article, article_year, members):
    sitting = {m.iso3 for m in members}
    incoming = parse_incoming(article, article_year, sitting)
    assert {m.iso3 for m in incoming} == {"ZWE", "KGZ", "TTO", "AUT", "PRT"}
    assert all(m.term_start == 2027 and m.term_end == 2028 for m in incoming)


def test_incoming_excludes_members_already_sitting(article, article_year, members):
    sitting = {m.iso3 for m in members}
    incoming = parse_incoming(article, article_year, sitting)
    assert not sitting & {m.iso3 for m in incoming}


def test_incoming_is_empty_before_the_election_is_written_up(article, members):
    # Asking for a year with no row yet is the pre-June state.
    assert parse_incoming(article, 2090, {m.iso3 for m in members}) == []


def test_current_membership_passes_the_guards(members, article, article_year):
    guards.check_current(members)
    sitting = {m.iso3 for m in members}
    guards.check_incoming(parse_incoming(article, article_year, sitting), article_year)
