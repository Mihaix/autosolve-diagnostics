"""
Task A5 — Merge All Data Sources into Final Corpus
====================================================
Combines all data sources into one final_corpus.json that Person B ingests
into the Chroma DB vector database.

Sources (all optional — handles missing files gracefully):
  - OBD code corpus (obd_corpus.json)
  - Ross-Tech wiki corpus (ross_tech_corpus.json)
  - BMW fault code knowledge base (bmw_fault_corpus.json)
  - PDF corpus files (pdf_corpus_*.json)
  - Dummy corpus (dummy_corpus.json)

Performs:
  - Schema validation
  - Deduplication by content hash
  - Unique chunk_id assignment
  - Summary statistics

Author: Person A — Data Engineer
"""

import json
import os
import re
import hashlib
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASETS_DIR = os.path.join(PROJECT_ROOT, "datasets")

OUTPUT_FILE = os.path.join(DATASETS_DIR, "final_corpus.json")

# Required metadata keys per the data contract
REQUIRED_METADATA_KEYS = ["make", "model", "year_range", "source_file", "page_number", "section"]

# Source files to merge (in priority order)
SOURCE_FILES = [
    ("dummy_corpus.json", "dummy"),
    ("obd_corpus.json", "obd"),
    ("ross_tech_corpus.json", "rosstech"),
    ("bmw_fault_corpus.json", "bmw"),
]

# Also pick up any pdf_corpus_*.json files
PDF_CORPUS_PATTERN = "pdf_corpus_*.json"


def validate_chunk(chunk: dict, source_name: str, index: int) -> list:
    """Validate a chunk against the data contract. Returns list of errors."""
    errors = []

    if not isinstance(chunk, dict):
        return [f"Chunk {index} from {source_name}: not a dictionary"]

    if "content" not in chunk:
        errors.append(f"Chunk {index} from {source_name}: missing 'content'")
    elif not isinstance(chunk["content"], str):
        errors.append(f"Chunk {index} from {source_name}: 'content' is not a string")
    elif len(chunk["content"].strip()) == 0:
        errors.append(f"Chunk {index} from {source_name}: 'content' is empty")

    if "metadata" not in chunk:
        errors.append(f"Chunk {index} from {source_name}: missing 'metadata'")
    elif not isinstance(chunk["metadata"], dict):
        errors.append(f"Chunk {index} from {source_name}: 'metadata' is not a dictionary")
    else:
        for key in REQUIRED_METADATA_KEYS:
            if key not in chunk["metadata"]:
                errors.append(f"Chunk {index} from {source_name}: missing metadata key '{key}'")

    return errors


def content_hash(text: str) -> str:
    """Generate a SHA-256 hash of the content for deduplication."""
    normalized = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]


def load_source(filename: str) -> list:
    """Load a JSON corpus file. Returns empty list if file doesn't exist."""
    filepath = os.path.join(DATASETS_DIR, filename)
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        else:
            print(f"  WARNING: {filename} is not a JSON array, skipping")
            return []
    except (json.JSONDecodeError, Exception) as e:
        print(f"  WARNING: Failed to load {filename}: {e}")
        return []


def main():
    print("=" * 60)
    print("Task A5 — Merge All Data Sources into Final Corpus")
    print("=" * 60)

    all_chunks = []
    source_stats = {}
    validation_errors = []

    # Load static source files
    for filename, prefix in SOURCE_FILES:
        print(f"\nLoading: {filename}...")
        data = load_source(filename)
        if data:
            print(f"  ✓ Loaded {len(data)} chunks")
            source_stats[filename] = len(data)

            # Validate each chunk
            for i, chunk in enumerate(data):
                errors = validate_chunk(chunk, filename, i)
                if errors:
                    validation_errors.extend(errors)
                else:
                    chunk["_source_prefix"] = prefix
                    all_chunks.append(chunk)
        else:
            print(f"  ○ Not found or empty, skipping")

    # Load PDF corpus files (glob pattern)
    print(f"\nSearching for PDF corpus files: {PDF_CORPUS_PATTERN}...")
    pdf_files = glob.glob(os.path.join(DATASETS_DIR, PDF_CORPUS_PATTERN))
    for filepath in sorted(pdf_files):
        filename = os.path.basename(filepath)
        print(f"\nLoading: {filename}...")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                print(f"  ✓ Loaded {len(data)} chunks")
                source_stats[filename] = len(data)

                for i, chunk in enumerate(data):
                    errors = validate_chunk(chunk, filename, i)
                    if errors:
                        validation_errors.extend(errors)
                    else:
                        # Derive prefix from filename
                        prefix = filename.replace("pdf_corpus_", "").replace(".json", "")
                        chunk["_source_prefix"] = f"pdf_{prefix}"
                        all_chunks.append(chunk)
        except Exception as e:
            print(f"  WARNING: Failed to load {filename}: {e}")

    # Report validation errors
    if validation_errors:
        print(f"\n⚠ Validation Errors ({len(validation_errors)}):")
        for err in validation_errors[:20]:  # Show first 20
            print(f"  - {err}")
        if len(validation_errors) > 20:
            print(f"  ... and {len(validation_errors) - 20} more")

    if not all_chunks:
        print("\nERROR: No valid chunks found from any source!")
        return

    # Deduplicate by content hash
    print(f"\nDeduplicating {len(all_chunks)} chunks...")
    seen_hashes = set()
    deduplicated = []
    duplicates = 0

    for chunk in all_chunks:
        h = content_hash(chunk["content"])
        if h not in seen_hashes:
            seen_hashes.add(h)
            deduplicated.append(chunk)
        else:
            duplicates += 1

    print(f"  Removed {duplicates} duplicate chunks")
    print(f"  Remaining: {len(deduplicated)} unique chunks")

    # Assign unique chunk IDs and clean up
    print(f"\nAssigning chunk IDs...")
    source_counters = {}
    final_corpus = []

    # Sort by source_file then section for reproducibility
    deduplicated.sort(key=lambda c: (
        c["metadata"].get("source_file", ""),
        c["metadata"].get("section", "")
    ))

    for chunk in deduplicated:
        prefix = chunk.pop("_source_prefix", "unknown")
        if prefix not in source_counters:
            source_counters[prefix] = 0
        source_counters[prefix] += 1

        chunk_id = f"{prefix}_{source_counters[prefix]:04d}"
        chunk["chunk_id"] = chunk_id

        final_corpus.append(chunk)

    # Save final corpus
    print(f"\nSaving final corpus to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_corpus, f, indent=2, ensure_ascii=False)

    # Summary statistics
    word_counts = [len(c["content"].split()) for c in final_corpus]
    avg_words = sum(word_counts) / len(word_counts)

    make_counts = {}
    source_file_counts = {}
    for c in final_corpus:
        make = c["metadata"]["make"]
        src = c["metadata"]["source_file"]
        make_counts[make] = make_counts.get(make, 0) + 1
        source_file_counts[src] = source_file_counts.get(src, 0) + 1

    print(f"\n{'='*60}")
    print(f"FINAL CORPUS SUMMARY")
    print(f"{'='*60}")
    print(f"  Total chunks:     {len(final_corpus)}")
    print(f"  Duplicates removed: {duplicates}")
    print(f"  Validation errors:  {len(validation_errors)}")
    print(f"")
    print(f"  Chunk size statistics:")
    print(f"    Average:  {avg_words:.0f} words")
    print(f"    Min:      {min(word_counts)} words")
    print(f"    Max:      {max(word_counts)} words")
    print(f"")
    print(f"  Chunks by source file:")
    for src, count in sorted(source_file_counts.items()):
        print(f"    {src}: {count}")
    print(f"")
    print(f"  Chunks by vehicle make:")
    for make, count in sorted(make_counts.items()):
        print(f"    {make}: {count}")
    print(f"")
    print(f"  Output: {OUTPUT_FILE}")
    print(f"  File size: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
