RFC — AutoSolve Diagnostics
Team size: 3

Submission deadline: End of Week 12

1. Introduction
AutoSolve Diagnostics is an LLM-based conversational agent designed to help everyday car owners, advanced DIY enthusiasts, and professional mechanics understand and resolve vehicle faults. The system accepts a natural language symptom description or an OBD-II diagnostic trouble code (DTC) as input and produces a clear, grounded explanation of the underlying problem along with a step-by-step repair procedure.

2. Problem Definition
Task type: Conditional text generation with grounded retrieval (Retrieval-Augmented Generation).

Input: A user query via a React frontend consisting of:

A natural language symptom description or an OBD-II diagnostic trouble code (e.g., P0420)

Vehicle context: Make, Model, and Year (e.g., Volkswagen Golf 2018)

Output: A structured JSON response containing:

A plain-language explanation of the identified fault and its root cause.

A step-by-step repair or diagnostic procedure.

Source citations indicating the originating document, section, and page number.

A boolean fallback flag indicating if the system had to resort to generic advice due to missing data.

Constraints and challenges:

Zero-tolerance hallucination policy. The system must not invent or infer technical specifications (torque values, clearances, part numbers). All generated content must be traceable to a retrieved document chunk.

Retrieval precision. The corpus spans multiple vehicles. A retrieval error returning specs for the wrong engine variant is a safety-relevant failure. Metadata filtering by vehicle identity (make and model) must be enforced at the database level prior to retrieval.

Strict Formatting: Smaller LLMs can struggle with JSON schema adherence. The backend must employ robust parsing (e.g., Regex) to guarantee frontend stability.

3. State of the Art
Current approaches to automated vehicle fault diagnosis and LLM-grounded question answering span several research directions:

[1] Retrieval-Augmented Generation (RAG)
Lewis, P. et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020.
The foundational work establishing the RAG paradigm. AutoSolve directly adopts this architecture, replacing the open-domain Wikipedia corpus with a domain-specific automotive technical corpus.

[2] Dense Passage Retrieval
Karpukhin, V. et al. (2020). Dense Passage Retrieval for Open-Domain Question Answering. EMNLP 2020.
Demonstrates that dense vector similarity retrieval substantially outperforms sparse BM25 retrieval for semantically complex queries — directly relevant to symptom-based queries.

[3] LLM Hallucination Mitigation
Huang, L. et al. (2023). A Survey on Hallucination in Large Language Models. arXiv.
Informs the design of AutoSolve's strict system prompting, confidence threshold routing, and graceful degradation (fallback mechanisms).

[4] OBD-II Standardisation and Fault Code Taxonomy
SAE International. SAE J1979 — E/E Diagnostic Test Modes.
The standardisation document defining OBD-II diagnostic trouble codes. Serves as the authoritative reference for the query expansion dictionary utilized in the AutoSolve backend.

4. Proposed Solution
Architecture: A decoupled RAG pipeline. A React frontend communicates via REST API with a FastAPI Python backend, utilizing LangChain as the orchestration framework to manage database retrieval and LLM interactions.

Pipeline overview:

Offline ingestion phase (Data Engineering):

PDF documents (manuals, TSBs) and web wikis are ingested and chunked using PyMuPDF or web scrapers.

Documents are formatted into a strict JSON schema containing the content and a metadata dictionary (make, model, year range, source file, page number).

Each chunk is embedded using sentence-transformers/all-MiniLM-L6-v2, producing a 384-dimensional dense vector.

Vectors and metadata are persisted in a local Chroma DB instance.

Online query phase (Backend API):

Query Expansion: The user's query is intercepted. If an OBD-II code (e.g., P0171) is detected, the backend performs an O(1) lookup against a local obd_codes.json dictionary and expands the query into a full semantic sentence (e.g., "P0171 System Too Lean fault code diagnosis repair symptoms").

The expanded query is embedded using the all-MiniLM-L6-v2 model.

Metadata Filtering: A hard-coded $and filter restricts the search space to documents matching the exact make and model before cosine similarity search retrieves the top 5 chunks.

Confidence Routing: The top score is evaluated against a tuned threshold (e.g., 0.20, calibrated for MiniLM's strict semantic scoring). If below the threshold, the system routes to a safe, non-technical fallback prompt.

Generation & Guardrails: The retrieved chunks are assembled into a prompt. A strict SystemMessage is injected to explicitly forbid the LLM from hallucinating repair steps or numerical values not found in the context.

Parsing: The LLM output is processed using a custom Regular Expression (Regex) parser to strip unexpected markdown, extract the required sections, and return a clean JSON payload to the frontend.

Frameworks and models:

Frontend Interface: React.js

Backend API: FastAPI (Python)

Orchestration: LangChain

Embedding Model: sentence-transformers/all-MiniLM-L6-v2 (384-dimensional vectors)

Vector Store: Chroma DB (local persistent)

LLM Backend: mistralai/Mistral-7B-Instruct-v0.2 served via Hugging Face Inference API (Featherless-AI provider)

5. Dataset
Dataset name: AutoSolve Technical Corpus v1

Sources:

OEM workshop and service manuals (sourced as publicly available PDFs)

Technical Service Bulletins (TSBs)

VAG-specific diagnostic wikis (e.g., Ross-Tech)

obd_codes.json: A static key-value dictionary based on the SAE J1979 taxonomy for dynamic query expansion.

Data Contracts:
The Data Engineering pipeline must output data in a strict JSON array format to be consumed by the Chroma DB ingestion script. Each item must contain:

content: The raw text chunk (approx. 150-400 words).

metadata: A dictionary containing make, model, year_range, source_file, page_number, and section.

This structure guarantees that the retrieval engine can isolate documents by specific vehicle chassis configurations, preventing cross-contamination of torque specifications or repair procedures.