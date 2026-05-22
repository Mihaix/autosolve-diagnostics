# RFC — AutoSolve Diagnostics
**Team size:** 3  
**Submission deadline:** End of Week 12

---

## 1. Introduction

AutoSolve Diagnostics is an LLM-based conversational agent designed to help everyday car owners, advanced DIY enthusiasts, and professional mechanics understand and resolve vehicle faults. The system accepts a natural language symptom description or an OBD-II diagnostic trouble code (DTC) as input and produces a clear, grounded explanation of the underlying problem along with a step-by-step repair procedure.

---

## 2. Problem Definition

**Task type:** Conditional text generation with grounded retrieval (Retrieval-Augmented Generation).

**Input:** A user query consisting of one or more of the following:
- A natural language symptom description (e.g., *"my engine stutters at idle and the check engine light is on"*)
- An OBD-II diagnostic trouble code (e.g., `P0420`)
- Vehicle context: make, model, and year (e.g., *Toyota Camry 2019*)

**Output:** A structured response containing:
1. A plain-language explanation of the identified fault and its root cause
2. A step-by-step repair or diagnostic procedure
3. A source citation indicating the originating document, section, and page number

**Constraints and challenges:**

- **Zero-tolerance hallucination policy.** The system must not invent or infer technical specifications (torque values, clearances, part numbers, fluid capacities). All generated content must be traceable to a retrieved document chunk. If no relevant document is found for the queried vehicle and fault combination, the system must explicitly acknowledge this and fall back to safe, generic guidance.
- **Retrieval precision.** The corpus spans multiple vehicle makes, models, and years. A retrieval error that returns a torque specification for the wrong engine variant is a safety-relevant failure. Metadata filtering by vehicle identity must be enforced at retrieval time.
- **Document heterogeneity.** Workshop manuals, TSBs, and repair guides differ significantly in structure, formatting, and terminology, requiring a robust and consistent ingestion pipeline.
- **User population diversity.** The system must produce output that is interpretable by both a professional mechanic and a non-technical car owner.

---

## 3. State of the Art

Current approaches to automated vehicle fault diagnosis and LLM-grounded question answering span several research directions:

**[1] Retrieval-Augmented Generation (RAG)**
Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020.
[https://arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401)
The foundational work establishing the RAG paradigm, in which a dense retriever conditions a sequence-to-sequence model on relevant external documents at inference time. AutoSolve directly adopts this architecture, replacing the open-domain Wikipedia corpus with a domain-specific automotive technical corpus.

**[2] Dense Passage Retrieval**
Karpukhin, V. et al. (2020). *Dense Passage Retrieval for Open-Domain Question Answering.* EMNLP 2020.
[https://arxiv.org/abs/2004.04906](https://arxiv.org/abs/2004.04906)
Demonstrates that dense vector similarity retrieval substantially outperforms sparse BM25 retrieval for semantically complex queries — directly relevant to symptom-based queries where the user's vocabulary may differ from manual terminology.

**[3] LLM Hallucination Mitigation**
Huang, L. et al. (2023). *A Survey on Hallucination in Large Language Models.* arXiv.
[https://arxiv.org/abs/2311.05232](https://arxiv.org/abs/2311.05232)
A comprehensive survey of hallucination types and mitigation strategies in LLMs. Informs the design of AutoSolve's retrieval confidence threshold and fallback mechanism.

**[4] Automotive Fault Diagnosis with Machine Learning**
Vachtsevanos, G. et al. (2006). *Intelligent Fault Diagnosis and Prognosis for Engineering Systems.* Wiley.
Covers classical ML approaches to fault classification in automotive and engineering systems. Provides a baseline for understanding the diagnostic problem prior to the LLM era.

**[5] OBD-II Standardisation and Fault Code Taxonomy**
SAE International. *SAE J1979 — E/E Diagnostic Test Modes.*
[https://www.sae.org/standards/content/j1979_201702/](https://www.sae.org/standards/content/j1979_201702/)
The standardisation document defining OBD-II diagnostic trouble codes and test modes. Serves as the authoritative reference for the fault code taxonomy used in corpus construction and query parsing.

---

## 4. Proposed Solution

**Architecture:** A RAG pipeline with a strict grounding constraint, implemented in Python using LangChain as the orchestration framework.

**Pipeline overview:**

*Offline ingestion phase (runs once, updated when corpus changes):*
1. PDF documents (manuals, TSBs, repair guides) are ingested using `PyMuPDF`, which preserves page structure and handles multi-column technical layouts.
2. Documents are segmented into overlapping chunks of approximately 400 tokens, with vehicle make/model/year extracted and stored as metadata alongside each chunk.
3. Each chunk is embedded using OpenAI `text-embedding-3-small`, producing a 1536-dimensional dense vector.
4. Vectors and metadata are persisted in a local **Chroma DB** instance, indexed for metadata pre-filtering.

*Online query phase (per user request):*
1. The user's input is parsed to extract the vehicle identity (make, model, year) and the fault descriptor (symptom text or OBD code).
2. The query string is embedded with the same model used at ingestion.
3. A metadata pre-filter restricts the search space to documents tagged for the queried vehicle before cosine similarity search retrieves the top-k most relevant chunks (k = 5).
4. The cosine similarity score of the top-1 result is evaluated against a tuned confidence threshold (initially 0.75). If the score falls below the threshold, the system routes to a safe fallback prompt that prohibits the LLM from generating any specific technical values.
5. Retrieved chunks, their source citations, and the user query are assembled into a structured prompt and passed to the LLM (`claude-sonnet-4-20250514` or `gpt-4o-mini` via API, abstracted behind LangChain's `BaseChatModel` interface for swappability).
6. The LLM generates a structured response: fault explanation, step-by-step repair procedure, and cited sources. A post-generation validation step checks that every factual claim is supported by at least one cited chunk.

**Frameworks and models:**
-Orchestration: LangChain (Python)
-Embedding: sentence-transformers/all-MiniLM-L6-v2
-Vector store: Chroma DB (local persistent)
-PDF ingestion: PyMuPDF (fitz)
-LLM backend: mistralai/Mistral-7B-Instruct-v0.2 served via the Hugging Face Inference API

---

## 5. Dataset

**Dataset name:** AutoSolve Technical Corpus v1

**Sources:**
- OEM workshop and service manuals (make/model/year-specific, sourced as publicly available PDFs)
- Technical Service Bulletins (TSBs) from manufacturer portals and [NHTSA TSB database](https://www.nhtsa.gov/vehicle/tsbs)
- Verified third-party repair guides (Haynes, Chilton series)
- OBD-II fault code reference database (based on SAE J1979 taxonomy, supplemented with make-specific extended codes)

**Description:** A curated collection of structured automotive technical documents covering a target set of vehicle makes, models, and model years to be finalised during corpus construction. Each document is tagged with vehicle metadata (make, model, year range, engine variant) to enable retrieval pre-filtering.

**Expected preprocessing steps:**
1. PDF text extraction using PyMuPDF, with page number and section header retention.
2. Heuristic cleaning to remove headers, footers, page numbers, and table-of-contents entries that do not carry diagnostic content.
3. Chunking into 400-token overlapping segments (50-token overlap) with metadata annotation per chunk.
4. Embedding generation and ingestion into Chroma DB.
5. Manual spot-check of a random sample of chunks to verify extraction fidelity, particularly for tables containing torque and clearance specifications.