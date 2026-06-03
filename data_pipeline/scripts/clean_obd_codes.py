"""
Task A2 — Clean OBD-II Code Library
====================================
Converts the raw obd-trouble-codes.json (which has a broken schema where
every object uses the first entry's code/description as KEYS) into:
  1. obd_codes.json       — Clean {code: description} dictionary for query expansion
  2. obd_corpus.json      — Corpus chunks for the vector database

Author: Person A — Data Engineer
"""

import json
import os
import re
import hashlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASETS_DIR = os.path.join(PROJECT_ROOT, "datasets")

RAW_FILE = os.path.join(DATASETS_DIR, "obd-trouble-codes.json")
CLEAN_DICT_FILE = os.path.join(DATASETS_DIR, "obd_codes.json")
CORPUS_FILE = os.path.join(DATASETS_DIR, "obd_corpus.json")


# ---------------------------------------------------------------------------
# OBD-II code category descriptions (for enriching corpus chunks)
# ---------------------------------------------------------------------------
CODE_CATEGORIES = {
    "P0": "Powertrain — Fuel and Air Metering / Auxiliary Emission Controls",
    "P01": "Powertrain — Fuel and Air Metering",
    "P02": "Powertrain — Fuel and Air Metering (Injector Circuit)",
    "P03": "Powertrain — Ignition System or Misfire",
    "P04": "Powertrain — Auxiliary Emissions Controls",
    "P05": "Powertrain — Vehicle Speed Controls and Idle Control System",
    "P06": "Powertrain — Computer Output Circuit",
    "P07": "Powertrain — Transmission",
    "P1": "Powertrain — Manufacturer Specific",
    "P2": "Powertrain — Generic (SAE Reserved)",
    "P3": "Powertrain — Generic / Manufacturer Specific",
    "B0": "Body — Generic",
    "B1": "Body — Manufacturer Specific",
    "C0": "Chassis — Generic",
    "C1": "Chassis — Manufacturer Specific",
    "U0": "Network Communication — Generic",
    "U1": "Network Communication — Manufacturer Specific",
}


def get_category(code: str) -> str:
    """Return the most specific category description for an OBD code."""
    # Try increasingly less specific prefixes
    for length in [3, 2, 1]:
        prefix = code[:length + 1] if length > 1 else code[0]
        # Try the full prefix match
        for cat_prefix, desc in CODE_CATEGORIES.items():
            if code.startswith(cat_prefix) and len(cat_prefix) == length + 1:
                return desc
    # Fallback
    if code.startswith("P"):
        return "Powertrain"
    elif code.startswith("B"):
        return "Body"
    elif code.startswith("C"):
        return "Chassis"
    elif code.startswith("U"):
        return "Network Communication"
    return "Unknown"


def clean_obd_codes():
    """Parse the broken JSON schema and extract clean code->description pairs."""
    print(f"Loading raw OBD codes from: {RAW_FILE}")
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"  Raw entries: {len(raw_data)}")

    codes = {}

    # The raw data structure is broken:
    # Each object has two key-value pairs:
    #   { "P0100": "P0XXX", "Mass or Volume Air Flow...": "Actual description" }
    # Where the KEYS are always P0100 and its description,
    # and the VALUES contain the actual code and description.
    #
    # We also need to capture P0100 itself from the first entry.

    # First, extract the "key" code (P0100) from the schema itself
    first_entry = raw_data[0] if raw_data else {}
    key_names = list(first_entry.keys())

    if len(key_names) == 2:
        # The first key IS a code (P0100), and the first value is the description key
        base_code = key_names[0]  # "P0100"
        base_desc = key_names[1]  # "Mass or Volume Air Flow Circuit Malfunction"

        # Add the base code itself
        codes[base_code] = base_desc

    # Now extract all actual codes from the values
    for entry in raw_data:
        values = list(entry.values())
        if len(values) == 2:
            code = str(values[0]).strip()
            description = str(values[1]).strip()

            # Validate it looks like an OBD code (P/B/C/U followed by digits)
            if re.match(r'^[PBCU]\d{4}$', code):
                # Clean up description (remove trailing semicolons, etc.)
                description = description.rstrip(';').strip()
                if description:
                    codes[code] = description

    # Sort by code
    sorted_codes = dict(sorted(codes.items()))

    print(f"  Extracted {len(sorted_codes)} unique OBD-II codes")
    print(f"  Code range: {list(sorted_codes.keys())[0]} — {list(sorted_codes.keys())[-1]}")

    # Spot check
    spot_checks = ["P0100", "P0171", "P0300", "P0420"]
    for sc in spot_checks:
        if sc in sorted_codes:
            print(f"  ✓ {sc}: {sorted_codes[sc][:60]}...")

    return sorted_codes


def generate_corpus_chunks(codes: dict) -> list:
    """
    Generate corpus chunks from OBD codes.
    These are tagged as 'generic' since they apply to all vehicles.
    We group related codes together for richer chunks.
    """
    chunks = []

    # Group codes by their first 4 characters (e.g., P010, P017) to create
    # semantically related chunks
    groups = {}
    for code, desc in codes.items():
        prefix = code[:4]  # e.g., "P010" groups P0100-P0109
        if prefix not in groups:
            groups[prefix] = []
        groups[prefix].append((code, desc))

    for prefix, code_list in sorted(groups.items()):
        # Build a readable chunk from the group
        category = get_category(code_list[0][0])

        lines = []
        lines.append(f"OBD-II Diagnostic Trouble Codes — {prefix}x Series")
        lines.append(f"Category: {category}")
        lines.append("")

        for code, desc in code_list:
            lines.append(f"• {code}: {desc}")

        lines.append("")
        lines.append(
            "These are standardized SAE J1979 diagnostic trouble codes. "
            "When any of these codes are present, the vehicle's Check Engine Light (MIL) "
            "will typically illuminate. Diagnosis should include reading freeze frame data, "
            "checking related sensor circuits, and inspecting associated components. "
            "Always clear codes after repair and verify they do not return during a drive cycle."
        )

        content = "\n".join(lines)

        chunk = {
            "content": content,
            "metadata": {
                "make": "generic",
                "model": "generic",
                "year_range": "all",
                "source_file": "obd_codes_library",
                "page_number": None,
                "section": f"OBD-II Codes {prefix}x"
            }
        }
        chunks.append(chunk)

    return chunks


def main():
    print("=" * 60)
    print("Task A2 — Clean OBD-II Code Library")
    print("=" * 60)

    # Step 1: Clean the raw codes
    codes = clean_obd_codes()

    # Step 2: Save clean dictionary
    print(f"\nSaving clean dictionary to: {CLEAN_DICT_FILE}")
    with open(CLEAN_DICT_FILE, "w", encoding="utf-8") as f:
        json.dump(codes, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(codes)} codes")

    # Step 3: Generate corpus chunks
    print(f"\nGenerating corpus chunks...")
    chunks = generate_corpus_chunks(codes)
    print(f"  Generated {len(chunks)} chunks")

    # Step 4: Save corpus
    print(f"Saving corpus to: {CORPUS_FILE}")
    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    # Summary
    word_counts = [len(c["content"].split()) for c in chunks]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Clean dictionary: {len(codes)} codes → {CLEAN_DICT_FILE}")
    print(f"  Corpus chunks:    {len(chunks)} chunks → {CORPUS_FILE}")
    print(f"  Avg chunk size:   {avg_words:.0f} words")
    print(f"  Min chunk size:   {min(word_counts)} words")
    print(f"  Max chunk size:   {max(word_counts)} words")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
