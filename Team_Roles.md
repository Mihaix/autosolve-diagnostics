# AutoSolve Diagnostics — Team Roles & Task Summary

---

## Person A — Data Engineer
**Role summary:** You are responsible for sourcing, cleaning, and
structuring all automotive data that feeds the system. The quality
of the entire project depends on the quality of your output.
Person B cannot build anything without your data.

---

**Task A1 — Create the Dummy JSON file**
Purpose: Unblock Person B immediately so they can start building
the pipeline without waiting for real data.
Output: A file called `dummy_corpus.json` with 5 realistic VW Golf
fault code entries in the agreed chunk format (content + metadata).
Deadline: Day 1.

---

**Task A2 — Build the OBD-II Code Library**
Purpose: Provide a structured reference of all standard SAE fault
codes so the system can identify any OBD-II code even before finding
it in a workshop manual.
Output: A clean `obd_codes.json` file converted from the GitHub
CSV dataset, ready to be ingested into the vector database.

---

**Task A3 — Build the Ross-Tech VCDS Wiki Scraper**
Purpose: The Ross-Tech Wiki is the most authoritative free source
for VAG-specific fault code context. Scraping it gives the system
real-world diagnostic knowledge written by VAG specialists.
Output: A script that automatically extracts fault code pages and
saves them as correctly formatted JSON chunks with metadata.

---

**Task A4 — Build the PDF Chunker for Workshop Manuals**
Purpose: Workshop manuals contain the torque specs, repair procedures,
and technical specifications the system needs to answer questions
accurately. The chunker breaks large PDFs into small indexed segments.
Output: A script that reads any workshop manual PDF and produces
correctly formatted JSON chunks with page numbers and section tags.

---

**Task A5 — Deliver the Final Merged Corpus**
Purpose: Combine all data sources into one single file that Person B
ingests into the vector database.
Output: A file called `final_corpus.json` containing all chunks from
all sources, consistently formatted and tagged with vehicle metadata.

---

## Person B — AI / Backend Architect
**Role summary:** You are the engine of the project. You build the
RAG pipeline that connects the data to the language model, and expose
it as an API that Person C's frontend can call. Your most critical
responsibility is enforcing the zero-hallucination policy.

---

**Task B1 — Set Up the Backend Environment**
Purpose: Establish a clean, reproducible Python environment that all
teammates can replicate with one command.
Output: A working virtual environment and a `requirements.txt` file
that installs all dependencies without errors.

---

**Task B2 — Build the Ingestion Pipeline**
Purpose: Read Person A's JSON corpus, generate vector embeddings for
every chunk, and store them in Chroma DB with their metadata.
This is the offline step that populates the knowledge base.
Output: A script that when run produces a populated local Chroma DB
containing all corpus chunks, searchable by semantic similarity
and filterable by vehicle make and model.

---

**Task B3 — Write the Anti-Hallucination Prompt**
Purpose: The prompt is the contract between your system and the LLM.
It explicitly instructs the model to answer only from provided context
and defines exactly what to say when no documentation is found.
Output: A prompt template file containing two prompts — one for
normal grounded responses and one for the fallback case.

---

**Task B4 — Build the RAG Retrieval Logic**
Purpose: When a user query arrives, find the most relevant chunks
from the database for that specific vehicle. The metadata filter
ensures a VW Golf query never returns a Toyota spec.
Output: A retrieval function that returns the top 5 most relevant
chunks for a given query, filtered by make and model, with a
confidence score attached to each result.

---

**Task B5 — Build the FastAPI Server**
Purpose: Expose the entire RAG pipeline as a web API so Person C
can connect the frontend to it with a single HTTP call.
Output: A running server with two endpoints — GET /health so Person C
can verify the server is live, and POST /diagnose which accepts a
vehicle and fault query and returns a structured diagnostic response.

---

**Task B6 — Test Both Pipeline Paths**
Purpose: Verify the system works correctly for both a known fault
(returns a grounded answer with sources) and an unknown fault
(triggers the fallback without inventing any information).
Output: Two confirmed test results — one normal response with
a confidence score above 0.75 and cited sources, and one fallback
response with is_fallback set to true and no invented specifications.

---

## Person C — Frontend Developer
**Role summary:** You build the interface that real users interact
with. Your job is to make the system's output clear and trustworthy,
especially communicating when the system is uncertain.

---

**Task C1 — Set Up the React Project**
Purpose: Establish the frontend development environment.
Output: A running React app accessible in the browser with a clean
empty starting point, ready for component development.

---

**Task C2 — Build the Input Form**
Purpose: Collect the four pieces of information the API needs —
vehicle make, model, year, and the fault query — and send them
to Person B's backend on submit.
Output: A form component with four fields and a submit button that
calls POST /diagnose and handles the loading state visually.

---

**Task C3 — Build the Results Display**
Purpose: Present the API response in a clear, readable layout that
both a mechanic and a non-technical user can follow.
Output: A result component that displays the problem explanation,
core cause, step-by-step solution, and source citations in clearly
labelled sections.

---

**Task C4 — Build the Fallback State**
Purpose: When the system has no verified data for a vehicle,
the user must see a clear warning — not a normal result that
looks authoritative. This is the frontend side of the
zero-hallucination policy.
Output: A visible warning banner that appears when is_fallback
is true, telling the user that no verified documentation was found
and that they should consult a certified technician.

---

**Task C5 — Full Integration Test**
Purpose: Verify the complete user journey works end to end —
from filling the form to seeing a real API response displayed.
Output: A working demo where a VW Golf P0420 query returns a
formatted result card, and a Ferrari query triggers the
fallback warning banner.

---

## Dependency Chain

Person A delivers dummy JSON on Day 1 → Person B builds and tests
the pipeline → Person B shares the API contract (the response format)
→ Person C builds the UI against that contract.

Person C does not need to wait for the real API to be ready.
They can build and style all components using hardcoded dummy
responses and swap in the real API call at the end.