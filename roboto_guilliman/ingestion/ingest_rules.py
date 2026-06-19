"""Parse rulebook PDFs and ingest chunked embeddings into Firestore."""

from __future__ import annotations

import argparse
import hashlib
import logging
from pathlib import Path

import fitz
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector

from roboto_guilliman.chunking import TextChunk, chunk_page_text
from roboto_guilliman.config import Settings, get_settings
from roboto_guilliman.embeddings import EmbeddingService
from roboto_guilliman.ingestion.source_registry import assert_ingestible_pdf

logger = logging.getLogger(__name__)


def extract_chunks_from_pdf(
    pdf_path: Path,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    doc = fitz.open(pdf_path)
    chunks: list[TextChunk] = []
    chunk_index = 0
    try:
        for page_number, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            if not page_text.strip():
                continue
            page_chunks = chunk_page_text(
                page_text,
                page_number=page_number,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                start_index=chunk_index,
            )
            chunks.extend(page_chunks)
            chunk_index += len(page_chunks)
    finally:
        doc.close()
    return chunks


def _chunk_doc_id(source: str, chunk: TextChunk) -> str:
    digest = hashlib.sha256(f"{source}:{chunk.page}:{chunk.chunk_index}".encode()).hexdigest()
    return digest[:32]


def ingest_to_firestore(
    chunks: list[TextChunk],
    *,
    settings: Settings,
    source_name: str,
    batch_size: int = 16,
    dry_run: bool = False,
) -> int:
    if not chunks:
        logger.warning("No chunks to ingest.")
        return 0

    db = firestore.Client(
        project=settings.gcp_project_id,
        database=settings.firestore_database,
    )
    collection = db.collection(settings.firestore_collection)
    embedder = EmbeddingService(settings)
    written = 0

    for start in range(0, len(chunks), batch_size):
        batch_chunks = chunks[start : start + batch_size]
        vectors = embedder.embed_documents([chunk.text for chunk in batch_chunks])
        batch = db.batch()

        for chunk, vector in zip(batch_chunks, vectors, strict=True):
            doc_id = _chunk_doc_id(source_name, chunk)
            payload = {
                "text": chunk.text,
                "embedding": Vector(vector),
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
                "source": source_name,
                "section_hint": chunk.section_hint,
            }
            if dry_run:
                logger.info("Dry run: would write %s (page %s)", doc_id, chunk.page)
            else:
                batch.set(collection.document(doc_id), payload)
            written += 1

        if not dry_run:
            batch.commit()
            logger.info("Committed batch %s-%s", start, start + len(batch_chunks) - 1)

    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest Warhammer 11th edition rule PDFs into Firestore vector search.",
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the core rules PDF (not committed to git).",
    )
    parser.add_argument(
        "--source-name",
        default="core_rules_11th",
        help="Logical source label stored on each chunk document.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk only; do not write to Firestore.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Embedding/write batch size.",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args()
    settings = get_settings()

    if not args.pdf_path.exists():
        raise SystemExit(f"PDF not found: {args.pdf_path}")

    assert_ingestible_pdf(args.pdf_path)

    logger.info("Extracting chunks from %s", args.pdf_path)
    chunks = extract_chunks_from_pdf(
        args.pdf_path,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    logger.info("Extracted %s chunks", len(chunks))

    count = ingest_to_firestore(
        chunks,
        settings=settings,
        source_name=args.source_name,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )
    logger.info("Ingestion complete: %s documents", count)


if __name__ == "__main__":
    main()
