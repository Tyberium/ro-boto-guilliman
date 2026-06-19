from roboto_guilliman.ingestion.download_rules import parse_api_hits
from roboto_guilliman.ingestion.source_registry import ParserProfile


def test_parse_api_hits_extracts_asset_links_and_dedupes() -> None:
    hits = [
        {
            "title": "#New40k - Core Rules",
            "download_categories": ["new40k"],
            "id": {"file": "new40k_core_rules.pdf"},
        },
        {
            "title": "Duplicate #New40k - Core Rules",
            "download_categories": ["new40k"],
            "id": {"file": "new40k_core_rules.pdf"},
        },
        {
            "title": "Core Rules",
            "download_categories": ["core-rules-and-key-downloads"],
            "id": {"file": "core_rules_sep2024.pdf"},
        },
        {
            "title": "Faction Pack: Orks",
            "download_categories": ["faction-packs"],
            "id": {"file": "orks.pdf"},
        },
    ]
    entries = parse_api_hits(hits)
    assert len(entries) == 3
    assert entries[0].title == "#New40k - Core Rules"
    assert entries[0].parser_profile == ParserProfile.CORE_RULES
    assert entries[0].relative_path.startswith("core_rules/")
    assert entries[1].title == "Core Rules"
    assert entries[1].parser_profile == ParserProfile.EXCLUDED
    assert entries[1].relative_path.startswith("excluded/")
    assert entries[2].title == "Faction Pack: Orks"
    assert entries[2].parser_profile == ParserProfile.FACTION_PACKS
