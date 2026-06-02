import os
import sys
import json
import re

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from huggingface_hub import InferenceClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.prompt_template import DIAGNOSTIC_PROMPT, FALLBACK_PROMPT

load_dotenv()

app = FastAPI(
    title="AutoSolve Diagnostics API",
    description="RAG-based automotive diagnostic agent",
    version="1.0.0"
)

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
    sources: List[str]
    confidence_score: float
    is_fallback: bool

CHROMA_PATH          = "./database/chroma_db"
COLLECTION_NAME      = "autosolve_diagnostics"
CONFIDENCE_THRESHOLD = 0.20

# LOAD OBD-II TROUBLE CODES DICTIONARY
OBD_CODES = {}
OBD_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'obd_codes.json')
try:
    with open(OBD_FILE_PATH, 'r', encoding='utf-8') as f:
        OBD_CODES = json.load(f)
    print(f"✓ Loaded {len(OBD_CODES)} OBD-II trouble codes")
except FileNotFoundError:
    print(f"⚠ Warning: OBD codes file not found at {OBD_FILE_PATH}")
except json.JSONDecodeError as e:
    print(f"✗ Error parsing OBD codes JSON: {e}")

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
    token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
)
print("Mistral connected. Server ready.")


# HELPER: DETECT OBD CODE IN QUERY
def extract_obd_code(query: str) -> str:
    """
    Extract OBD-II code from query if present.
    Returns the code (e.g., 'P0420') or None if not found.
    OBD codes format: Letter (P/C/U/B) + 4 digits
    """
    match = re.search(r'([PCUB]\d{4})', query.upper())
    if match:
        return match.group(1)
    return None


# HELPER: EXPAND OBD QUERY
def expand_query_with_obd(query: str) -> str:
    """
    If query contains OBD code, expand it with its meaning
    for better semantic similarity matching.
    
    Example:
    Input:  "P0420"
    Output: "P0420 Catalyst System Efficiency Below Threshold Bank 1 
             catalytic converter efficiency diagnosis repair"
    """
    obd_code = extract_obd_code(query)
    
    if obd_code and obd_code in OBD_CODES:
        description = OBD_CODES[obd_code]
        # Expand query with code meaning for better retrieval
        expanded = f"{obd_code} {description} fault code diagnosis repair symptoms causes"
        print(f"[QUERY EXPANSION] {obd_code} → expanded for semantic search")
        return expanded
    
    # If no OBD code or not in dictionary, use original query
    return query


# HELPER: CALL THE LLM
def call_llm(prompt: str) -> str:
    response = hf_client.chat_completion(
        messages=[
            {"role": "system", "content": "You are a strict diagnostic parser. You MUST NOT invent, guess, or hallucinate any repair steps, symptoms, or numerical values. If a step is not explicitly written in the provided context, you must not output it."},
            {"role": "user", "content": prompt}
        ],
        model="mistralai/Mistral-7B-Instruct-v0.2",
        max_tokens=1024,
        temperature=0.1
    )
    return response.choices[0].message.content


# HELPER: PARSE LLM RESPONSE
def parse_llm_response(text: str) -> dict:
    sections = {
        "problem_elaboration": "",
        "core_cause": "",
        "solution": "",
        "sources": []
    }
    current_section = None
    
    # 1. Strip out markdown bolding/headers Mistral might have hallucinated
    clean_text = text.replace("**", "").replace("###", "")
    lines = clean_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line: 
            continue
        
        upper_line = line.upper()
        
        # 2. Use regex to find the header and grab any text on the same line
        if "PROBLEM EXPLANATION" in upper_line:
            current_section = "problem_elaboration"
            content = re.split(r'PROBLEM EXPLANATION[\-\:]*', line, flags=re.IGNORECASE)[-1].strip()
            if content: sections[current_section] += content + " "
            
        elif "CORE CAUSE" in upper_line:
            current_section = "core_cause"
            content = re.split(r'CORE CAUSE[\-\:]*', line, flags=re.IGNORECASE)[-1].strip()
            if content: sections[current_section] += content + " "
            
        elif "STEP-BY-STEP SOLUTION" in upper_line or "SOLUTION" in upper_line:
            current_section = "solution"
            content = re.split(r'(?:STEP-BY-STEP SOLUTION|SOLUTION)[\-\:]*', line, flags=re.IGNORECASE)[-1].strip()
            if content: sections[current_section] += content + " "
            
        elif "SOURCES" in upper_line:
            current_section = "sources"
            
        else:
            # 3. Append normal lines to whatever section is currently active
            if current_section == "sources":
                # Clean up bullet points or numbers Mistral might add to sources
                clean_source = re.sub(r'^[\-\*\d\.]+\s*', '', line)
                if clean_source: 
                    sections["sources"].append(clean_source)
            elif current_section:
                sections[current_section] += line + " "

    # 4. Clean up trailing/leading whitespace and stray dashes
    for key in ["problem_elaboration", "core_cause", "solution"]:
        # .strip() removes spaces, .lstrip('-') removes leading dashes
        sections[key] = sections[key].strip().lstrip('-').strip()

    # Fallback if the LLM completely ignored the format
    if not sections["solution"]:
        sections["solution"] = text.strip().lstrip('-').strip()

    return sections


# ENDPOINT 1: HEALTH CHECK
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model": "Mistral-7B-Instruct-v0.2",
        "embedding": "all-MiniLM-L6-v2",
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "obd_codes_loaded": len(OBD_CODES)
    }


# ENDPOINT 2: DIAGNOSTIC QUERY
@app.post("/diagnose", response_model=DiagnosticResponse)
def diagnose(request: DiagnosticRequest):
    """
    Diagnostic endpoint following RFC Section 4 - Online query phase:
    1. Parse & expand query (OBD code + vehicle context)
    2. Retrieve relevant documents with metadata pre-filter
    3. Check confidence threshold
    4. Route to fallback or normal LLM path
    5. Generate structured response
    6. Return with source citations
    """

    # RFC STEP 1: PARSE & EXPAND QUERY
    # Extract vehicle identity (make, model, year) and fault descriptor
    expanded_query = expand_query_with_obd(request.query)
    
    print(f"\n[QUERY] make={request.make}, model={request.model}, year={request.year}")
    print(f"[QUERY] original: {request.query}")
    print(f"[QUERY] expanded: {expanded_query}")

    # RFC STEP 2-3: RETRIEVE WITH METADATA PRE-FILTER
    try:
        results = vector_store.similarity_search_with_relevance_scores(
            query=expanded_query,  # Use expanded query for better retrieval
            k=5,
            filter={
                "$and": [
                    {"make":  {"$eq": request.make}},
                    {"model": {"$eq": request.model}}
                ]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval error: {str(e)}"
        )

    # RFC STEP 4: CONFIDENCE CHECK
    top_score = results[0][1] if results else 0.0
    print(f"[RETRIEVAL] Top confidence score: {top_score:.4f} (threshold: {CONFIDENCE_THRESHOLD})")

    # RFC STEP 4B: FALLBACK PATH (LOW CONFIDENCE)
    if top_score < CONFIDENCE_THRESHOLD:
        print(f"[FALLBACK] Score {top_score:.4f} below threshold {CONFIDENCE_THRESHOLD}")
        fallback_prompt = FALLBACK_PROMPT.format(question=request.query)
        try:
            fallback_text = call_llm(fallback_prompt)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"LLM error (fallback): {str(e)}"
            )

        return DiagnosticResponse(
            problem_elaboration=fallback_text.strip(),
            core_cause="Could not be determined — no verified documentation found.",
            solution="Please consult a certified technician or the official workshop manual for your specific vehicle.",
            sources=[],
            confidence_score=round(top_score, 4),
            is_fallback=True
        )

    # RFC STEP 4A: NORMAL PATH (HIGH CONFIDENCE)
    print(f"[LLM] Generating response with {len(results)} context chunks")
    context_parts = []
    source_list   = []

    for doc, score in results:
        context_parts.append(doc.page_content)
        source_file = doc.metadata.get("source_file", "Unknown document")
        page_number = doc.metadata.get("page_number", "?")
        section     = doc.metadata.get("section", "")
        citation    = f"{source_file} — Page {page_number}"
        if section:
            citation += f" ({section})"
        if citation not in source_list:
            source_list.append(citation)

    context = "\n\n".join(context_parts)
    
    # RFC STEP 5: ASSEMBLE PROMPT (use original query, not expanded)
    # This ensures LLM answers what user actually asked
    diag_prompt  = DIAGNOSTIC_PROMPT.format(
        context=context,
        question=request.query
    )

    try:
        llm_response = call_llm(diag_prompt)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM error: {str(e)}"
        )

    # RFC STEP 6: PARSE & RETURN
    parsed = parse_llm_response(llm_response)

    return DiagnosticResponse(
        problem_elaboration=parsed["problem_elaboration"],
        core_cause=parsed["core_cause"],
        solution=parsed["solution"],
        sources=source_list,
        confidence_score=round(top_score, 4),
        is_fallback=False
    )