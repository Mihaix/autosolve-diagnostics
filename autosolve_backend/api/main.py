import os
import sys

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
CONFIDENCE_THRESHOLD = 0.10

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


# -------------------------------------------------------
# HELPER — call the LLM using chat_completion
#
# WHY chat_completion and not text_generation:
# HuggingFace routes Mistral-7B-Instruct through featherless-ai
# which only supports the conversational (chat) interface.
# chat_completion sends the prompt as a user message,
# which is exactly what that provider expects.
# -------------------------------------------------------
def call_llm(prompt: str) -> str:
    response = hf_client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model="mistralai/Mistral-7B-Instruct-v0.2",
        max_tokens=1024,
        temperature=0.1
    )
    return response.choices[0].message.content


# -------------------------------------------------------
# HELPER — parse the LLM text response into fields
# -------------------------------------------------------
def parse_llm_response(text: str) -> dict:
    sections = {
        "problem_elaboration": "",
        "core_cause": "",
        "solution": "",
        "sources": []
    }
    current_section = None
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()

        if "PROBLEM EXPLANATION" in line.upper():
            current_section = "problem_elaboration"
        elif "CORE CAUSE" in line.upper():
            current_section = "core_cause"
        elif "STEP-BY-STEP SOLUTION" in line.upper() or "SOLUTION" in line.upper():
            current_section = "solution"
        elif "SOURCES" in line.upper():
            current_section = "sources"
        elif current_section == "sources" and line:
            sections["sources"].append(line)
        elif current_section and line and "---" not in line:
            if current_section != "sources":
                sections[current_section] += line + " "

    for key in ["problem_elaboration", "core_cause", "solution"]:
        sections[key] = sections[key].strip()

    if not sections["solution"]:
        sections["solution"] = text.strip()

    return sections


# -------------------------------------------------------
# ENDPOINT 1 — GET /health
# -------------------------------------------------------
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model": "Mistral-7B-Instruct-v0.2",
        "embedding": "all-MiniLM-L6-v2",
        "confidence_threshold": CONFIDENCE_THRESHOLD
    }


# -------------------------------------------------------
# ENDPOINT 2 — POST /diagnose
# -------------------------------------------------------
@app.post("/diagnose", response_model=DiagnosticResponse)
def diagnose(request: DiagnosticRequest):

    # STEP 1 — RETRIEVE
    try:
        results = vector_store.similarity_search_with_relevance_scores(
            query=request.query,
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

    # STEP 2 — CONFIDENCE CHECK
    top_score = results[0][1] if results else 0.0

    # STEP 3B — FALLBACK PATH
    if top_score < CONFIDENCE_THRESHOLD:
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

    # STEP 3A — NORMAL PATH
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

    context      = "\n\n".join(context_parts)
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

    # STEP 4 — PARSE + RETURN
    parsed = parse_llm_response(llm_response)

    return DiagnosticResponse(
        problem_elaboration=parsed["problem_elaboration"],
        core_cause=parsed["core_cause"],
        solution=parsed["solution"],
        sources=source_list,
        confidence_score=round(top_score, 4),
        is_fallback=False
    )