from pathlib import Path

import pytest

from roboto_guilliman.ingestion.source_registry import (
    ParserProfile,
    assert_ingestible_pdf,
    resolve_parser_profile,
    source_slug,
)


@pytest.mark.parametrize(
    ("title", "gw_category", "expected"),
    [
        ("Core Rules", "core-rules-and-key-downloads", ParserProfile.EXCLUDED),
        (
            "Quick Start Guide",
            "core-rules-and-key-downloads",
            ParserProfile.EXCLUDED,
        ),
        (
            "Core Rules Updates and Rules Commentary",
            "core-rules-and-key-downloads",
            ParserProfile.UPDATES_AND_FAQ,
        ),
        ("Balance Dataslate", "core-rules-and-key-downloads", ParserProfile.REFERENCE),
        (
            "Pariah Nexus Tournament Companion",
            "core-rules-and-key-downloads",
            ParserProfile.EVENT_COMPANIONS,
        ),
        ("Faction Pack: Orks", "faction-packs", ParserProfile.FACTION_PACKS),
        ("Faction Pack: Orks", "new40k", ParserProfile.FACTION_PACKS),
        ("#New40k - Core Rules", "new40k", ParserProfile.CORE_RULES),
        ("Warhammer Event Companion", "event-companions", ParserProfile.EVENT_COMPANIONS),
        ("Boarding Actions Companion", "miscellaneous", ParserProfile.MISCELLANEOUS),
    ],
)
def test_resolve_parser_profile(title: str, gw_category: str, expected: ParserProfile) -> None:
    layout = resolve_parser_profile(title=title, gw_category=gw_category)
    assert layout.parser_profile == expected
    assert layout.folder == expected


def test_source_slug_strips_faction_prefix() -> None:
    assert source_slug("Faction Pack: Space Marines") == "space_marines"


def test_assert_ingestible_pdf_rejects_excluded(tmp_path: Path) -> None:
    excluded = tmp_path / "excluded" / "core_rules.pdf"
    excluded.parent.mkdir(parents=True)
    excluded.write_bytes(b"%PDF-1.4")
    with pytest.raises(SystemExit, match="Refusing to ingest"):
        assert_ingestible_pdf(excluded, rules_dir=tmp_path)
