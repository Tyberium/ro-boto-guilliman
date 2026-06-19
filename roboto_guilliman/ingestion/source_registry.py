"""Map GW download metadata to local folders and ingest parser profiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

DEFAULT_RULES_DIR = Path("data/rules")


class ParserProfile(StrEnum):
    """Chunking strategy applied when ingesting a PDF."""

    CORE_RULES = "core_rules"
    UPDATES_AND_FAQ = "updates_and_faq"
    REFERENCE = "reference"
    FACTION_PACKS = "faction_packs"
    EVENT_COMPANIONS = "event_companions"
    MISCELLANEOUS = "miscellaneous"
    EXCLUDED = "excluded"


INGESTIBLE_PROFILES = frozenset(
    profile for profile in ParserProfile if profile is not ParserProfile.EXCLUDED
)


@dataclass(frozen=True)
class SourceLayout:
    parser_profile: ParserProfile
    folder: str


def resolve_parser_profile(*, title: str, gw_category: str) -> SourceLayout:
    """Pick folder + parser from GW API category and download title."""
    normalized = title.strip().lower()

    if normalized == "core rules":
        return SourceLayout(
            ParserProfile.EXCLUDED,
            ParserProfile.EXCLUDED,
        )
    if "quick start" in normalized:
        return SourceLayout(ParserProfile.EXCLUDED, ParserProfile.EXCLUDED)

    if "faction pack" in normalized:
        return SourceLayout(ParserProfile.FACTION_PACKS, ParserProfile.FACTION_PACKS)

    if gw_category == "event-companions":
        return SourceLayout(ParserProfile.EVENT_COMPANIONS, ParserProfile.EVENT_COMPANIONS)

    if gw_category == "miscellaneous":
        return SourceLayout(ParserProfile.MISCELLANEOUS, ParserProfile.MISCELLANEOUS)

    if gw_category == "core-rules-and-key-downloads":
        if "core rules updates" in normalized or "rules commentary" in normalized:
            return SourceLayout(ParserProfile.UPDATES_AND_FAQ, ParserProfile.UPDATES_AND_FAQ)
        if normalized in {"balance dataslate", "munitorum field manual"}:
            return SourceLayout(ParserProfile.REFERENCE, ParserProfile.REFERENCE)
        if "tournament companion" in normalized or "chapter approved" in normalized:
            return SourceLayout(ParserProfile.EVENT_COMPANIONS, ParserProfile.EVENT_COMPANIONS)

    if gw_category == "new40k" and "core rules" in normalized:
        return SourceLayout(ParserProfile.CORE_RULES, ParserProfile.CORE_RULES)

    if gw_category in {"faction-packs", "new40k"}:
        return SourceLayout(ParserProfile.FACTION_PACKS, ParserProfile.FACTION_PACKS)

    return SourceLayout(ParserProfile.MISCELLANEOUS, ParserProfile.MISCELLANEOUS)


def profile_from_path(
    pdf_path: Path,
    *,
    rules_dir: Path = DEFAULT_RULES_DIR,
) -> ParserProfile | None:
    try:
        relative = pdf_path.resolve().relative_to(rules_dir.resolve())
        return ParserProfile(relative.parts[0])
    except (ValueError, IndexError):
        return None


def assert_ingestible_pdf(pdf_path: Path, *, rules_dir: Path = DEFAULT_RULES_DIR) -> ParserProfile:
    profile = profile_from_path(pdf_path, rules_dir=rules_dir)
    if profile == ParserProfile.EXCLUDED:
        raise SystemExit(
            f"Refusing to ingest {pdf_path.name}: files under data/rules/excluded/ are "
            "local reference only (e.g. Sep 2024 layout core rules without rule numbers). "
            "Use data/rules/core_rules/#New40k PDF for Firestore ingest."
        )
    if profile is None:
        raise SystemExit(
            f"Refusing to ingest {pdf_path}: place PDFs under data/rules/{{parser_profile}}/ "
            "or pass an ingestible profile path."
        )
    return profile


def source_slug(title: str) -> str:
    """Stable ingest label derived from the GW download title."""
    slug = title.lower()
    if slug.startswith("faction pack:"):
        slug = slug.removeprefix("faction pack:").strip()
    slug = slug.replace("#new40k - ", "")
    slug = slug.replace(" ", "_").replace("-", "_")
    slug = "".join(char for char in slug if char.isalnum() or char == "_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "unknown"
