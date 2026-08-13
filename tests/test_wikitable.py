from unsc.wikitable import Table, split_top_level

# Two-year terms mean a country's cell spans rows, so row 2 has fewer raw
# cells than columns. This is the whole reason the module exists.
ROWSPAN_TABLE = """{| class="wikitable"
! Year !! A !! B
|-
! 1966
| rowspan="2" | {{flagwrap|Mali}} || {{flagwrap|Jordan}}
|-
! 1967
| {{flagwrap|India}}
|}"""


def test_split_ignores_pipes_inside_templates():
    assert split_top_level("{{flagwrap|Japan|1947}} || {{flagwrap|Chad}}", "||") == [
        "{{flagwrap|Japan|1947}} ",
        " {{flagwrap|Chad}}",
    ]


def test_split_ignores_pipes_inside_wikilinks():
    assert split_top_level("[[A|B]]||[[C|D]]", "||") == ["[[A|B]]", "[[C|D]]"]


def test_rowspan_carries_into_the_next_row():
    rows = Table.parse(ROWSPAN_TABLE).rows
    assert rows[1].texts == ["1966", "{{flagwrap|Mali}}", "{{flagwrap|Jordan}}"]
    assert rows[2].texts == ["1967", "{{flagwrap|Mali}}", "{{flagwrap|India}}"]


def test_colspan_widens_a_header():
    table = Table.parse(
        '{| class="wikitable"\n! Year !! colspan="2" | Africa\n|-\n| 1966 || X || Y\n|}'
    )
    assert table.header.texts == ["Year", "Africa", "Africa"]


def test_attributes_are_stripped_but_content_with_equals_is_kept():
    table = Table.parse('{| class="wikitable"\n| width="10%" | [[A|B=C]]\n|}')
    assert table.rows[0][0].text == "[[A|B=C]]"


def test_parses_each_table_separately(article):
    tables = article.tables("Current membership")
    assert len(tables) == 2
    assert len(tables[0].rows) == 6  # header + P5
    assert len(tables[1].rows) == 11  # header + ten elected
