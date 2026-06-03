"""
Task A3 — Ross-Tech VCDS Wiki Scraper (Golf 5 TDI Relevant Only)
================================================================
Scrapes fault code pages from the Ross-Tech Wiki that are relevant to the
VW Golf 5 1.9 TDI (BKC engine). Outputs formatted corpus chunks.

The Ross-Tech Wiki uses VAG's internal 5-digit fault code numbering.
Each page has a predictable structure:
  - Title: "{5-digit code} - Description"
  - Sections: Possible Symptoms, Possible Causes, Possible Solutions, Special Notes

Only codes relevant to the Golf 5 1.9 TDI PD diesel are scraped.

Author: Person A — Data Engineer
"""

import json
import os
import re
import time
import sys

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install requests beautifulsoup4")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASETS_DIR = os.path.join(PROJECT_ROOT, "datasets")

RAW_DIR = os.path.join(DATASETS_DIR, "ross_tech_raw")
CORPUS_FILE = os.path.join(DATASETS_DIR, "ross_tech_corpus.json")

BASE_URL = "https://wiki.ross-tech.com/wiki/index.php/"
CATEGORY_URL = BASE_URL + "Category:Fault_Codes"

HEADERS = {
    "User-Agent": "AutoSolve-DataPipeline/1.0 (University Project; educational use only)"
}

# Polite delay between requests (seconds)
REQUEST_DELAY = 0.5

# ---------------------------------------------------------------------------
# Golf 5 1.9 TDI BKC — Relevant fault code ranges (VAG 5-digit codes)
# ---------------------------------------------------------------------------
# These are the VAG internal code ranges that are relevant to the Golf 5
# 1.9 TDI PD engine and associated systems. We include engine management,
# fuel system, turbo, EGR, glow plugs, exhaust, and general powertrain.
#
# VAG 5-digit to P-code mapping:
#   P0xxx = 16384 + decimal(0xxx)  →  VAG codes 16384–16895 map to P0000–P0511
#   P1xxx = 16896 + ...            →  etc.
#   P2xxx = 17408 + ...
#
# But many VAG-specific codes are in the 00xxx and 01xxx range (proprietary).
#
# We define relevance broadly: engine, turbo, diesel-specific, transmission,
# sensors, and generic OBD codes that these TDIs commonly throw.
# ---------------------------------------------------------------------------

# VAG proprietary code ranges relevant to 1.9 TDI
# These cover: engine sensors, fuel system, turbo, EGR, glow plugs,
# ABS/ESP (common on Golf 5), convenience modules
RELEVANT_VAG_RANGES = [
    (3, 3),           # Speed signal
    (96, 120),        # Coolant, oil pressure, steering
    (256, 300),       # Fuel injection, idle speed
    (435, 475),       # Brake system, steering angle
    (515, 560),       # Brake electronics, ABS
    (575, 600),       # Intake manifold, throttle
    (628, 670),       # Boost pressure, turbo, EGR
    (741, 800),       # ECU, CAN bus
    (810, 870),       # Glow plugs, preheating
    (883, 935),       # Sensors (MAF, MAP, temp, lambda)
    (943, 980),       # Injection timing, quantity
    (1008, 1050),     # Airbag, seatbelt
    (1117, 1140),     # Immobilizer, key
    (1164, 1230),     # Power windows, door modules
    (1259, 1262),     # Additional
]

# P-code equivalent ranges (stored as VAG 5-digit: 16384 + P0xxx decimal)
# P0100-P0199 (MAF, MAP, IAT, ECT, TPS) → VAG 16484-16583
# P0200-P0299 (Injectors, fuel pump)     → VAG 16584-16683
# P0300-P0399 (Misfires, ignition)       → VAG 16684-16783
# P0400-P0499 (EGR, evap, secondary air) → VAG 16784-16883
# P0500-P0599 (Speed, idle control)      → VAG 16884-16983
# P0600-P0699 (ECU, serial comm)         → VAG 16984-17083
# P1000-P1999 (Manufacturer specific)    → VAG 17384-18383
# P2000-P2999                            → VAG 18384-19383
RELEVANT_PCODE_RANGES = [
    (16384, 16983),   # P0000–P0599 (general powertrain)
    (16984, 17083),   # P0600–P0699 (ECU/communication)
    (17384, 17884),   # P1000–P1500 (VAG manufacturer specific)
    (18384, 18584),   # P2000–P2200 (later generic codes)
]


def is_relevant_code(code_str: str) -> bool:
    """Check if a VAG 5-digit fault code is relevant to Golf 5 1.9 TDI."""
    try:
        code_num = int(code_str)
    except ValueError:
        return True  # If we can't parse it, include it anyway

    # Check VAG proprietary ranges
    for start, end in RELEVANT_VAG_RANGES:
        if start <= code_num <= end:
            return True

    # Check P-code equivalent ranges
    for start, end in RELEVANT_PCODE_RANGES:
        if start <= code_num <= end:
            return True

    return False


def collect_fault_code_urls() -> list:
    """
    Crawl all pagination pages of Category:Fault_Codes to collect
    every fault code URL listed in the wiki.
    """
    all_codes = []
    url = CATEGORY_URL
    page_num = 0

    while url:
        page_num += 1
        print(f"  Fetching category page {page_num}: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  ERROR fetching category page: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Find all fault code links in the category listing
        # They are in <div class="mw-category"> → <li> → <a>
        category_div = soup.find("div", class_="mw-category")
        if category_div:
            for li in category_div.find_all("li"):
                link = li.find("a")
                if link and link.get("href"):
                    code_title = link.get("title", link.text).strip()
                    code_href = link["href"]
                    all_codes.append({
                        "code": code_title,
                        "url": "https://wiki.ross-tech.com" + code_href
                    })

        # Find the "next page" link
        next_link = None
        for a_tag in soup.find_all("a"):
            if a_tag.text.strip() == "next page":
                next_link = "https://wiki.ross-tech.com" + a_tag["href"]
                break

        url = next_link
        if url:
            time.sleep(REQUEST_DELAY)

    print(f"  Total codes found in wiki: {len(all_codes)}")
    return all_codes


def filter_relevant_codes(all_codes: list) -> list:
    """Filter the codes to only those relevant to Golf 5 1.9 TDI."""
    relevant = [c for c in all_codes if is_relevant_code(c["code"])]
    print(f"  Relevant codes for Golf 5 TDI: {len(relevant)} / {len(all_codes)}")
    return relevant


def scrape_fault_code_page(url: str) -> dict:
    """
    Scrape a single fault code page and extract structured data.

    Returns dict with:
      - title: Full page title
      - vag_code: 5-digit VAG code
      - p_code: Standard P-code (if found)
      - sections: dict of section_name → content text
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    ERROR: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Get the page title from h1
    h1 = soup.find("h1", id="firstHeading")
    title = h1.get_text(strip=True) if h1 else "Unknown"

    # Try to extract the P-code from the title
    # Format is often: "NNNNN/PXXXX/NNNNNN" or just the title text
    p_code_match = re.search(r'P\d{4}', title)
    p_code = p_code_match.group(0) if p_code_match else None

    # Extract the VAG code
    vag_code_match = re.match(r'(\d{5})', title)
    vag_code = vag_code_match.group(1) if vag_code_match else None

    # Find the content area
    content_div = soup.find("div", class_="mw-parser-output")
    if not content_div:
        content_div = soup.find("div", id="mw-content-text")

    sections = {}
    current_section = "Overview"
    current_content = []

    if content_div:
        for element in content_div.find_all(['h2', 'h3', 'h4', 'ul', 'ol', 'p']):
            if not hasattr(element, 'name') or element.name is None:
                continue

            # Check if this is a heading (h2, h3, or h4)
            if element.name in ['h2', 'h3', 'h4']:
                # Save the previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                    current_content = []

                # Get the heading text (strip edit links)
                headline = element.find("span", class_="mw-headline")
                if headline:
                    current_section = headline.get_text(strip=True)
                else:
                    current_section = element.get_text(strip=True)

            elif element.name == 'ul':
                # Extract list items
                for li in element.find_all('li'):
                    text = li.get_text(strip=True)
                    if text:
                        current_content.append(f"• {text}")

            elif element.name == 'ol':
                # Extract ordered list items
                for i, li in enumerate(element.find_all('li'), 1):
                    text = li.get_text(strip=True)
                    if text:
                        current_content.append(f"{i}. {text}")

            elif element.name in ['p', 'div']:
                text = element.get_text(strip=True)
                if text:
                    current_content.append(text)

        # Save the last section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

    return {
        "title": title,
        "vag_code": vag_code,
        "p_code": p_code,
        "url": url,
        "sections": sections
    }


def format_as_corpus_chunk(scraped: dict) -> dict:
    """Convert a scraped fault code page into a corpus chunk."""
    # Build readable content from all sections
    lines = []
    lines.append(f"Fault Code: {scraped['title']}")
    if scraped['p_code']:
        lines.append(f"Standard OBD-II Code: {scraped['p_code']}")
    lines.append("")

    for section_name, section_content in scraped['sections'].items():
        if section_name.lower() in ['overview', 'special notes', 'possible symptoms',
                                      'possible causes', 'possible solutions']:
            lines.append(f"--- {section_name} ---")
            lines.append(section_content)
            lines.append("")

    content = "\n".join(lines).strip()

    # Build section title for metadata
    section_title = scraped['title']
    if scraped['p_code'] and scraped['p_code'] not in section_title:
        section_title = f"{scraped['title']} ({scraped['p_code']})"

    chunk = {
        "content": content,
        "metadata": {
            "make": "Volkswagen",
            "model": "Golf 5",
            "year_range": "2003-2008",
            "source_file": "ross_tech_wiki",
            "page_number": None,
            "section": section_title
        }
    }

    return chunk


def main():
    print("=" * 60)
    print("Task A3 — Ross-Tech VCDS Wiki Scraper")
    print("       (Golf 5 1.9 TDI Relevant Codes Only)")
    print("=" * 60)

    # Ensure raw directory exists
    os.makedirs(RAW_DIR, exist_ok=True)

    # Step 1: Collect all fault code URLs from category pages
    print("\nStep 1: Collecting fault code URLs from category pages...")
    all_codes = collect_fault_code_urls()

    if not all_codes:
        print("ERROR: No fault codes found. Check network connection.")
        return

    # Step 2: Filter to relevant codes only
    print("\nStep 2: Filtering to Golf 5 TDI relevant codes...")
    relevant_codes = filter_relevant_codes(all_codes)

    # Step 3: Scrape each relevant fault code page
    print(f"\nStep 3: Scraping {len(relevant_codes)} fault code pages...")
    print(f"  Estimated time: ~{len(relevant_codes) * REQUEST_DELAY / 60:.1f} minutes")

    corpus_chunks = []
    errors = 0

    for i, code_info in enumerate(relevant_codes, 1):
        code = code_info["code"]
        url = code_info["url"]

        # Replace invalid path characters (like slashes) with underscores
        safe_filename = code.replace("/", "_").replace("\\", "_")

        print(f"  [{i}/{len(relevant_codes)}] Scraping {code}...", end=" ")

        # Check if we already have this cached
        raw_file = os.path.join(RAW_DIR, f"{safe_filename}.json")
        if os.path.exists(raw_file):
            print("(cached)")
            with open(raw_file, "r", encoding="utf-8") as f:
                scraped = json.load(f)
        else:
            scraped = scrape_fault_code_page(url)
            if scraped is None:
                print("FAILED")
                errors += 1
                continue

            # Save raw data
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(scraped, f, indent=2, ensure_ascii=False)
            print(f"OK ({len(scraped.get('sections', {}))} sections)")

            # Polite delay
            time.sleep(REQUEST_DELAY)

        # Format as corpus chunk
        chunk = format_as_corpus_chunk(scraped)

        # Only include chunks with meaningful content (>30 words)
        word_count = len(chunk["content"].split())
        if word_count >= 30:
            corpus_chunks.append(chunk)

    # Step 4: Save corpus
    print(f"\nStep 4: Saving corpus...")
    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        json.dump(corpus_chunks, f, indent=2, ensure_ascii=False)

    # Summary
    word_counts = [len(c["content"].split()) for c in corpus_chunks]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Total pages scraped:    {len(relevant_codes)}")
    print(f"  Errors:                 {errors}")
    print(f"  Corpus chunks created:  {len(corpus_chunks)}")
    print(f"  Avg chunk size:         {avg_words:.0f} words")
    print(f"  Output file:            {CORPUS_FILE}")
    print(f"  Raw data:               {RAW_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
