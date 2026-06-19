"""PDF chunking parsers keyed by parser profile."""

from roboto_guilliman.ingestion.parsers.core_rules import CoreRuleChunk, parse_core_rules_pdf

__all__ = ["CoreRuleChunk", "parse_core_rules_pdf"]
