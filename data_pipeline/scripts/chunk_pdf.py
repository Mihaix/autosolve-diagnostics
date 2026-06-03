"""
Task A4 — PDF Chunker for Workshop Manuals
============================================
Extracts text from workshop manual PDFs, splits into semantically meaningful
chunks (~200-350 words), and tags with vehicle metadata.

Uses PyMuPDF (fitz) for text extraction with font-size heuristics to detect
section headings and create meaningful chunk boundaries.

Usage:
  python chunk_pdf.py --input <pdf_path> --make <make> --model <model> --year_range <years> --output <output.json>

Examples:
  python scripts/chunk_pdf.py --input "datasets/raw_pdfs/4-cylinder diesel engine (1.9 l engine).pdf" --make "Volkswagen" --model "Golf 5" --year_range "2003-2008" --output datasets/pdf_corpus_vw_engine.json

  python scripts/chunk_pdf.py --input "datasets/raw_pdfs/E46_Bentley_Service_Manual.pdf" --make "BMW" --model "E46 330d" --year_range "1999-2005" --output datasets/pdf_corpus_bmw_bentley.json

Author: Person A — Data Engineer
"""

import json
import os
import re
import sys
import argparse

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed. Run: pip install PyMuPDF")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MIN_CHUNK_WORDS = 150    # Minimum words per chunk
TARGET_CHUNK_WORDS = 300 # Target chunk size
MAX_CHUNK_WORDS = 400    # Maximum words per chunk (split if exceeded)
HEADING_FONT_SIZE = 12.0 # Font size threshold to detect headings


def clean_text(text: str) -> str:
    """Clean extracted text: remove excessive whitespace, page artifacts."""
    # Remove form feed characters
    text = text.replace('\x0c', '')

    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove lines that are just page numbers
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines, pure page numbers, or very short lines that look like headers/footers
        if not stripped:
            cleaned_lines.append('')
            continue
        if re.match(r'^\d{1,4}$', stripped):
            continue  # Skip standalone page numbers
        if re.match(r'^Page \d+', stripped, re.IGNORECASE):
            continue  # Skip "Page N" lines
        if re.match(r'^-\s*\d+\s*-$', stripped):
            continue  # Skip "- N -" page markers
        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    # Collapse multiple blank lines into one
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_pages_with_headings(pdf_path: str) -> list:
    """
    Extract text from each page, using font-size analysis to detect headings.

    Returns a list of dicts:
      {page_num: int, text: str, headings: [str, ...]}
    """
    print(f"  Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    print(f"  Total pages: {len(doc)}")

    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Get plain text for the page
        text = page.get_text("text")
        text = clean_text(text)

        # Get font info to detect headings
        headings = []
        try:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_size = span.get("size", 0)
                        span_text = span.get("text", "").strip()
                        flags = span.get("flags", 0)

                        # Detect headings: larger font OR bold text with reasonable length
                        is_bold = bool(flags & 2**4)  # Bold flag
                        is_heading = (
                            (font_size >= HEADING_FONT_SIZE and len(span_text) > 3) or
                            (is_bold and font_size >= 10.0 and 3 < len(span_text) < 100)
                        )

                        if is_heading and span_text and not re.match(r'^\d+$', span_text):
                            headings.append(span_text)
        except Exception:
            pass  # If font analysis fails, proceed without headings

        if text and len(text.split()) > 5:  # Skip nearly empty pages
            pages.append({
                "page_num": page_num + 1,  # 1-indexed
                "text": text,
                "headings": headings
            })

    doc.close()
    print(f"  Extracted {len(pages)} non-empty pages")
    return pages


def split_into_sentences(text: str) -> list:
    """Split text into sentences for clean chunk boundaries."""
    # Split on sentence-ending punctuation followed by space or newline
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_pages(pages: list, source_filename: str) -> list:
    """
    Chunk the extracted pages into semantically meaningful segments.

    Strategy:
    1. Split text by paragraphs (double newline)
    2. Accumulate paragraphs into a buffer
    3. Flush when buffer reaches target size or a new heading is detected
    4. Track the most recent heading as the chunk's section context
    """
    chunks = []
    buffer_text = []
    buffer_words = 0
    current_section = "General"
    current_page_start = 1

    for page in pages:
        page_num = page["page_num"]

        # Update current section from detected headings
        if page["headings"]:
            # Use the first heading found on this page
            new_heading = page["headings"][0]
            # If we have a buffer and there's a heading change, flush
            if buffer_text and new_heading != current_section:
                chunk_text = "\n".join(buffer_text).strip()
                if len(chunk_text.split()) >= MIN_CHUNK_WORDS // 2:
                    chunks.append({
                        "text": chunk_text,
                        "page_start": current_page_start,
                        "page_end": page_num - 1 if page_num > 1 else 1,
                        "section": current_section
                    })
                buffer_text = []
                buffer_words = 0
                current_page_start = page_num

            current_section = new_heading

        # Split page text into paragraphs
        paragraphs = page["text"].split("\n\n")

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_words = len(para.split())

            # If adding this paragraph would exceed max, flush current buffer
            if buffer_words + para_words > MAX_CHUNK_WORDS and buffer_text:
                chunk_text = "\n".join(buffer_text).strip()
                if len(chunk_text.split()) >= MIN_CHUNK_WORDS // 2:
                    chunks.append({
                        "text": chunk_text,
                        "page_start": current_page_start,
                        "page_end": page_num,
                        "section": current_section
                    })
                buffer_text = []
                buffer_words = 0
                current_page_start = page_num

            buffer_text.append(para)
            buffer_words += para_words

            # If we've reached target size, flush
            if buffer_words >= TARGET_CHUNK_WORDS:
                chunk_text = "\n".join(buffer_text).strip()
                chunks.append({
                    "text": chunk_text,
                    "page_start": current_page_start,
                    "page_end": page_num,
                    "section": current_section
                })
                buffer_text = []
                buffer_words = 0
                current_page_start = page_num

    # Flush remaining buffer
    if buffer_text:
        chunk_text = "\n".join(buffer_text).strip()
        if len(chunk_text.split()) >= MIN_CHUNK_WORDS // 4:
            chunks.append({
                "text": chunk_text,
                "page_start": current_page_start,
                "page_end": pages[-1]["page_num"] if pages else 1,
                "section": current_section
            })

    # Handle oversized chunks by splitting at sentence boundaries
    final_chunks = []
    for chunk in chunks:
        words = chunk["text"].split()
        if len(words) > MAX_CHUNK_WORDS * 1.5:
            # Split this chunk
            sentences = split_into_sentences(chunk["text"])
            sub_buffer = []
            sub_words = 0
            for sentence in sentences:
                s_words = len(sentence.split())
                if sub_words + s_words > TARGET_CHUNK_WORDS and sub_buffer:
                    final_chunks.append({
                        "text": " ".join(sub_buffer),
                        "page_start": chunk["page_start"],
                        "page_end": chunk["page_end"],
                        "section": chunk["section"]
                    })
                    sub_buffer = []
                    sub_words = 0
                sub_buffer.append(sentence)
                sub_words += s_words
            if sub_buffer:
                final_chunks.append({
                    "text": " ".join(sub_buffer),
                    "page_start": chunk["page_start"],
                    "page_end": chunk["page_end"],
                    "section": chunk["section"]
                })
        else:
            final_chunks.append(chunk)

    return final_chunks


def format_corpus(chunks: list, make: str, model: str, year_range: str,
                  source_filename: str) -> list:
    """Format chunks into the data contract schema."""
    corpus = []
    for chunk in chunks:
        entry = {
            "content": chunk["text"],
            "metadata": {
                "make": make,
                "model": model,
                "year_range": year_range,
                "source_file": source_filename,
                "page_number": chunk["page_start"],
                "section": chunk["section"]
            }
        }
        corpus.append(entry)
    return corpus


def main():
    parser = argparse.ArgumentParser(
        description="Chunk a workshop manual PDF into corpus entries"
    )
    parser.add_argument("--input", required=True, help="Path to the input PDF file")
    parser.add_argument("--make", required=True, help="Vehicle make (e.g., Volkswagen)")
    parser.add_argument("--model", required=True, help="Vehicle model (e.g., Golf 5)")
    parser.add_argument("--year_range", required=True, help="Year range (e.g., 2003-2008)")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    parser.add_argument("--heading_size", type=float, default=HEADING_FONT_SIZE,
                        help=f"Font size threshold for heading detection (default: {HEADING_FONT_SIZE})")

    args = parser.parse_args()

    print("=" * 60)
    print("Task A4 — PDF Chunker for Workshop Manuals")
    print("=" * 60)
    print(f"  Input:      {args.input}")
    print(f"  Vehicle:    {args.make} {args.model} ({args.year_range})")
    print(f"  Output:     {args.output}")

    if not os.path.exists(args.input):
        print(f"\nERROR: Input file not found: {args.input}")
        sys.exit(1)

    source_filename = os.path.basename(args.input)

    # Step 1: Extract text with heading detection
    print(f"\nStep 1: Extracting text from PDF...")
    pages = extract_pages_with_headings(args.input)

    if not pages:
        print("ERROR: No text extracted from PDF. It may be scanned/image-based.")
        sys.exit(1)

    # Step 2: Chunk the text
    print(f"\nStep 2: Chunking text...")
    chunks = chunk_pages(pages, source_filename)
    print(f"  Created {len(chunks)} raw chunks")

    # Step 3: Format into corpus
    print(f"\nStep 3: Formatting corpus...")
    corpus = format_corpus(chunks, args.make, args.model, args.year_range, source_filename)

    # Step 4: Save
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    # Summary
    word_counts = [len(c["content"].split()) for c in corpus]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

    sections = set(c["metadata"]["section"] for c in corpus)

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Input PDF:        {source_filename}")
    print(f"  Pages processed:  {len(pages)}")
    print(f"  Chunks created:   {len(corpus)}")
    print(f"  Avg chunk size:   {avg_words:.0f} words")
    print(f"  Min chunk size:   {min(word_counts) if word_counts else 0} words")
    print(f"  Max chunk size:   {max(word_counts) if word_counts else 0} words")
    print(f"  Unique sections:  {len(sections)}")
    print(f"  Output file:      {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
