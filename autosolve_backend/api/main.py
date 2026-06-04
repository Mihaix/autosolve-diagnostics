import os
import sys
import json
import re

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from huggingface_hub import InferenceClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prompt_template import DIAGNOSTIC_PROMPT, FALLBACK_PROMPT,GENERAL_KNOWLEDGE_PROMPT

load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not HF_TOKEN:
    raise ValueError("Missing HuggingFace token in .env (set HUGGINGFACE_TOKEN)")

app = FastAPI(title="AutoSolve Diagnostics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiagnosticRequest(BaseModel):
    make: str
    model: str
    year: int
    query: str

class DiagnosticResponse(BaseModel):
    problem_elaboration: str
    core_cause: str
    solution: str
    sources: list[str]
    confidence_score: float
    is_fallback: bool


CHROMA_PATH          = "./database/chroma_db"
COLLECTION_NAME      = "autosolve_diagnostics"
CONFIDENCE_THRESHOLD = 0.20

OBD_CODES = {}
OBD_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'obd_codes.json')
try:
    with open(OBD_FILE_PATH, 'r', encoding='utf-8') as f:
        OBD_CODES = json.load(f)
    print(f"Loaded {len(OBD_CODES)} OBD-II codes.")
except FileNotFoundError:
    print(f"Warning: obd_codes.json not found at {OBD_FILE_PATH}. Continuing without it.")

print("Loading embedding model...")
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
print("Embedding model loaded.")

print("Connecting to Chroma DB...")
vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedding_model,
    persist_directory=CHROMA_PATH
)
print("Chroma DB connected.")

print("Connecting to Mistral via HuggingFace...")
hf_client = InferenceClient(
    provider="featherless-ai",
    token=HF_TOKEN
)
print("Mistral connected. Server ready.")


HEADER_RE = re.compile(
    r'^\s*-{2,}\s*(PROBLEM EXPLANATION|CORE CAUSE|STEP-BY-STEP SOLUTION)\s*-{2,}\s*$',
    re.IGNORECASE
)

SECTION_MAP = {
    "PROBLEM EXPLANATION": "problem_elaboration",
    "CORE CAUSE":          "core_cause",
    "STEP-BY-STEP SOLUTION": "solution",
}

def expand_query(query: str) -> str:
    q = query.strip()

    # Standard OBD-II: letter + 4 digits (P0420, C1234, etc.)
    obd_match = re.search(r'([PCUB]\d{4})', q.upper())
    if obd_match:
        code = obd_match.group(1)
        description = OBD_CODES.get(code, "")
        if description:
            return f"{code} {description} diagnosis"
        return code

    # VAG-specific numeric code: 4 or 5 digits only
    vag_match = re.fullmatch(r'\d{4,5}', q)
    if vag_match:
        return f"Fault Code: {q}"

    # Natural language query
    return q



def rerank(results: list, original_query: str) -> list:
    query_lower = original_query.strip().lower()
    boosted = []

    for doc, score in results:
        if query_lower in doc.page_content.lower():
            boosted.append((doc, score, score + 1.0))  # (doc, original, boosted)
        else:
            boosted.append((doc, score, score))

    # Sort by boosted score, highest first
    boosted.sort(key=lambda x: x[2], reverse=True)

    # Return top 5 as (doc, original_score) tuples
    return [(doc, original_score) for doc, original_score, _ in boosted[:5]]


def call_llm(prompt: str) -> str:
    response = hf_client.chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict automotive diagnostic assistant. "
                    "Never invent repair steps, part numbers, or file names. "
                    "Answer only from the provided context. "
                    "Keep responses concise and never repeat yourself."
                )
            },
            {"role": "user", "content": prompt}
        ],
        model="mistralai/Mistral-7B-Instruct-v0.2",
        max_tokens=1024,
        temperature=0.1
    )
    return response.choices[0].message.content


def parse_response(text: str) -> dict:
    sections = {
        "problem_elaboration": "",
        "core_cause": "",
        "solution": "",
    }
    current_section = None

    # Strip common LLM stop tokens and markdown noise
    clean = (text
             .replace("**", "")
             .replace("###", "")
             .replace("</s>", "")
             .replace("<|im_end|>", ""))

    for line in clean.strip().split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Test for exact header match FIRST — strict anchoring
        header_match = HEADER_RE.match(stripped)
        if header_match:
            key = header_match.group(1).upper()
            current_section = SECTION_MAP.get(key)
            continue  # header line itself is never content

        # Ignore hallucinated source lines even if parser enters them
        if stripped.lower().startswith("source") and "---" in stripped:
            current_section = None
            continue

        # Append content to active section
        if current_section:
            sections[current_section] += stripped + " "

    # Final cleanup
    for key in sections:
        sections[key] = sections[key].strip().lstrip("-").strip()

    # Safety net: if the LLM ignored the format entirely,
    # store the raw response in solution so nothing is lost
    if not any(sections.values()):
        sections["solution"] = text.strip()

    return sections

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model": "Mistral-7B-Instruct-v0.2",
        "embedding": "all-MiniLM-L6-v2",
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "obd_codes_loaded": len(OBD_CODES)
    }


@app.post("/diagnose", response_model=DiagnosticResponse)
async def diagnose_vehicle(request: DiagnosticRequest):

    search_query = expand_query(request.query)

    try:
        raw_results = vector_store.similarity_search_with_relevance_scores(
            query=search_query,
            k=15,
            filter={
                "$and": [
                    {"make":  {"$eq": request.make}},
                    {"model": {"$eq": request.model}}
                ]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

    # results = rerank(raw_results, request.query)
    # top_score = results[0][1] if results else 0.0

    # if not results or top_score < CONFIDENCE_THRESHOLD:
    #     return DiagnosticResponse(
    #         problem_elaboration="No relevant documentation was found for this vehicle and fault combination.",
    #         core_cause="Could not be determined — no verified documentation found.",
    #         solution="Please consult a certified technician or the official workshop manual for your specific vehicle.",
    #         sources=[],
    #         confidence_score=0.0,
    #         is_fallback=True
    #     )

    # context_parts = []
    # source_list   = []

    # for i, (doc, _) in enumerate(results, 1):
    #     # Context: neutral label only — no file names visible to LLM
    #     context_parts.append(f"[Document {i}]\n{doc.page_content}")

    #     # Sources: built from metadata, completely independent of LLM
    #     source_file = doc.metadata.get("source_file", "Unknown document")
    #     page_number = doc.metadata.get("page_number", "?")
    #     section     = doc.metadata.get("section", "")
    #     citation    = f"{source_file} — Page {page_number}"
    #     if section:
    #         citation += f" ({section})"
    #     if citation not in source_list:
    #         source_list.append(citation)

    # context = "\n\n".join(context_parts)

    # prompt = DIAGNOSTIC_PROMPT.format(
    #     context=context,
    #     question=request.query
    # )


    # try:
    #     llm_text = call_llm(prompt)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # parsed = parse_response(llm_text)

    # # Cap display score at 0.99 (boosted exact-match scores > 1.0)
    # display_score = min(round(float(top_score), 4), 0.99)

    # return DiagnosticResponse(
    #     problem_elaboration=parsed["problem_elaboration"],
    #     core_cause=parsed["core_cause"],
    #     solution=parsed["solution"],
    #     sources=source_list,   # from metadata
    #     confidence_score=display_score,
    #     is_fallback=False
    # )
    results = rerank(raw_results, request.query)
    top_score = results[0][1] if results else 0.0

    # 1. Determine if we have Good Data or Missing Data
    code_match = re.search(r'([PCUB]\d{4}|\d{4,5})', request.query.upper())
    is_missing_data = False

    if not results:
        is_missing_data = True
    elif code_match:
        # THE FIX: Check if the exact code physically exists in the Top Document's text
        target_code = code_match.group(1).lower()
        top_doc_text = results[0][0].page_content.lower()
        
        # If the re-ranker couldn't find the code to put it at the top, it's missing!
        if target_code not in top_doc_text:
            is_missing_data = True
    elif top_score < 0.20:
        is_missing_data = True

    # 2. The Prompt Router (Keep your existing code below this...)
    context_parts = []
    source_list = []

    if is_missing_data:
        # PATH A: General Knowledge Fallback (No DB Data)
        prompt = GENERAL_KNOWLEDGE_PROMPT.format(
            make=request.make,
            model=request.model,
            year=request.year,
            question=request.query
        )
        source_list = ["General AI Knowledge (No verified manuals found)"]
        display_score = 0.50  # Hardcode a medium score so the user knows it's a guess
    
    else:
        # PATH B: Standard Strict RAG (DB Data Found)
        for i, (doc, _) in enumerate(results, 1):
            context_parts.append(f"[Document {i}]\n{doc.page_content}")
            source_file = doc.metadata.get("source_file", "Unknown document")
            page_number = doc.metadata.get("page_number", "?")
            section = doc.metadata.get("section", "")
            
            citation = f"{source_file} — Page {page_number}"
            if section:
                citation += f" ({section})"
            if citation not in source_list:
                source_list.append(citation)

        context = "\n\n".join(context_parts)
        prompt = DIAGNOSTIC_PROMPT.format(
            context=context,
            question=request.query
        )
        display_score = min(round(float(top_score), 4), 0.99)

    # 3. Call the LLM and Parse (Works for both paths!)
    try:
        llm_text = call_llm(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    parsed = parse_response(llm_text)

    # Return the final JSON
    return DiagnosticResponse(
        problem_elaboration=parsed["problem_elaboration"],
        core_cause=parsed["core_cause"],
        solution=parsed["solution"],
        sources=source_list,
        confidence_score=display_score,
        is_fallback=False  # Keep false so the UI renders the AI's general steps!
    )