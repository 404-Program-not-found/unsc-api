import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unsc.wiki import Article  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
REVID = 1363842260


@pytest.fixture(scope="session")
def article() -> Article:
    """Real article wikitext, captured 2026-08."""
    text = (FIXTURES / "article-2026-08.wikitext").read_text(encoding="utf-8")
    return Article(wikitext=text, revid=REVID)


@pytest.fixture(scope="session")
def article_year() -> int:
    return 2026
