"""Print sample chunks from a rules PDF without writing to Firestore."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from roboto_guilliman.ingestion.parsers.core_rules import CoreRuleChunk, parse_core_rules_pdf
from roboto_guilliman.ingestion.source_registry import ParserProfile, profile_from_path

logger = logging.getLogger(__name__)

DEFAULT_RULES_DIR = Path("data/rules")


def _profile_from_path(pdf_path: Path) -> ParserProfile | None:
    return profile_from_path(pdf_path, rules_dir=DEFAULT_RULES_DIR)


def _format_chunk(chunk: CoreRuleChunk, *, max_chars: int) -> str:
    header = f"[{chunk.chunk_index}] Rule {chunk.rule_number} | {chunk.title} | page {chunk.page}"
    body = chunk.text if len(chunk.text) <= max_chars else f"{chunk.text[:max_chars]}…"
    return f"{header}\n{'-' * len(header)}\n{body}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print sample chunks from a rules PDF (no Firestore write).",
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        nargs="?",
        help="Path to a rules PDF. Defaults to the only file in data/rules/core_rules/.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of chunks to print (default: 20).",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip the first N chunks (default: 0).",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=600,
        help="Truncate each chunk body for terminal output (default: 600).",
    )
    parser.add_argument(
        "--profile",
        choices=[profile.value for profile in ParserProfile],
        help="Override parser profile inferred from the PDF path.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print chunk count summary only.",
    )
    return parser


def _default_core_rules_pdf() -> Path:
    folder = DEFAULT_RULES_DIR / ParserProfile.CORE_RULES
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs in {folder}. Run download-rules first.")
    for path in pdfs:
        if "new40k" in path.name.lower():
            return path
    if len(pdfs) == 1:
        return pdfs[0]
    names = "\n".join(f"  {path.name}" for path in pdfs)
    raise SystemExit(
        "Multiple core rules PDFs found and none match #New40k numbering. "
        f"Pass pdf_path explicitly:\n{names}"
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args()
    pdf_path = args.pdf_path or _default_core_rules_pdf()

    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    if _profile_from_path(pdf_path) == ParserProfile.EXCLUDED:
        raise SystemExit(
            f"{pdf_path.name} is under data/rules/excluded/ (not indexed). "
            "Use the #New40k core rules PDF in data/rules/core_rules/."
        )

    profile = ParserProfile(args.profile) if args.profile else None
    parsed = parse_core_rules_pdf(pdf_path)

    if args.stats:
        print(f"PDF: {pdf_path.name}")
        print(f"Profile: {profile or _profile_from_path(pdf_path)}")
        print(f"Chunks: {len(parsed)}")
        if parsed:
            print(f"First rule: {parsed[0].rule_number} ({parsed[0].title})")
            print(f"Last rule:  {parsed[-1].rule_number} ({parsed[-1].title})")
        return

    if profile and profile != ParserProfile.CORE_RULES:
        raise SystemExit(
            f"Preview parser for {profile!r} is not implemented yet. "
            "Only core_rules is supported."
        )
    if not profile and _profile_from_path(pdf_path) != ParserProfile.CORE_RULES:
        raise SystemExit("Only core_rules PDFs are supported for preview.")

    chunks = parsed[args.offset : args.offset + args.limit]
    if not chunks:
        raise SystemExit("No chunks matched. Check offset/limit or PDF content.")

    logger.info(
        "Showing chunks %s-%s of %s from %s",
        args.offset,
        args.offset + len(chunks) - 1,
        len(parsed),
        pdf_path.name,
    )
    for chunk in chunks:
        print(_format_chunk(chunk, max_chars=args.max_chars))
        print()


if __name__ == "__main__":
    main()
