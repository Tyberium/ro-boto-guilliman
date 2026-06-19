from roboto_guilliman.ingestion.parsers.core_rules import parse_core_rules_text


SAMPLE = """
CORE RULES
ACTIVE PLAYER AND OPPOSING PLAYER 01.03
The player whose turn it is is the Active Player.
BATTLE-SHOCK TESTS 02.01
When a unit fails a Battle-shock test, apply the effect below.
"""


def test_parse_core_rules_text_splits_on_rule_numbers() -> None:
    page_starts = [(0, 1)]
    chunks = parse_core_rules_text(SAMPLE, page_starts=page_starts)
    assert len(chunks) == 2
    assert chunks[0].rule_number == "01.03"
    assert chunks[0].title == "ACTIVE PLAYER AND OPPOSING PLAYER"
    assert "Active Player" in chunks[0].text
    assert chunks[1].rule_number == "02.01"
    assert chunks[1].title == "BATTLE-SHOCK TESTS"


def test_parse_core_rules_text_returns_empty_without_headers() -> None:
    assert parse_core_rules_text("intro only", page_starts=[(0, 1)]) == []
