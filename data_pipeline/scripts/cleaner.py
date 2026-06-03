import json
import re

# Update these paths if your file is in a different folder
INPUT_FILE = "./datasets/final_corpus.json"
OUTPUT_FILE = "clean_corpus.json"

def clean_corpus():
    print(f"Loading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {INPUT_FILE}")
        return

    # This regex matches the shattered "Protected by copyright..." 
    # through "...Volkswagen AG." regardless of how many newlines are inside it.
    watermark_regex = re.compile(
        r'P[\s\n]*r[\s\n]*o[\s\n]*t[\s\n]*e[\s\n]*c[\s\n]*t[\s\n]*e[\s\n]*d[\s\n]*b[\s\n]*y[\s\n]*c[\s\n]*o[\s\n]*p[\s\n]*y[\s\n]*r[\s\n]*i[\s\n]*g[\s\n]*h[\s\n]*t.*?'
        r'V[\s\n]*o[\s\n]*l[\s\n]*k[\s\n]*s[\s\n]*w[\s\n]*a[\s\n]*g[\s\n]*e[\s\n]*n[\s\n]*A[\s\n]*G\.',
        re.IGNORECASE | re.DOTALL
    )

    print("Cleaning text chunks...")
    cleaned_count = 0
    for item in data:
        original_text = item["content"]
        
        # 1. Nuke the scattered watermark
        text = watermark_regex.sub('', original_text)
        
        # 2. Replace all remaining newlines with spaces (best practice for vector math)
        text = text.replace('\n', ' ')
        
        # 3. Clean up any double spaces caused by the replacements
        text = re.sub(r'\s{2,}', ' ', text)
        
        # 4. Save the clean text back to the object
        item["content"] = text.strip()
        cleaned_count += 1

    print(f"Saving {cleaned_count} cleaned chunks to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # indent=2 keeps the JSON formatted nicely so you can read it
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Done! Your clean data is saved as {OUTPUT_FILE}.")

if __name__ == "__main__":
    clean_corpus()