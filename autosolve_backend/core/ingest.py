import json
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


CORPUS_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'dummy_corpus.json')
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'database', 'chroma_db')
COLLECTION_NAME = "autosolve_diagnostics"

def load_json_corpus(filepath: str) -> list:
    """Reads the JSON corpus provided by the Data Engineer."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Corpus not found at {filepath}. Make sure Person A delivered the JSON!")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    print("Initializing offline ingestion pipeline...")

    # Step 1: Load the raw JSON data
    print("Loading corpus...")
    raw_data = load_json_corpus(CORPUS_FILE_PATH)
    
    # Step 2: Transform JSON into LangChain Document objects
    # This specifically separates the 'content' for vectorization while keeping 'metadata' intact for hard-filtering later.
    documents = []
    for item in raw_data:
        doc = Document(
            page_content=item.get("content", ""),
            metadata=item.get("metadata", {})
        )
        documents.append(doc)
    
    print(f"Prepared {len(documents)} document chunks for embedding.")

    # Step 3: Initialize the local HuggingFace embedding model
    print("Spinning up all-MiniLM-L6-v2 embedding model (this may take a moment to download on first run)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Step 4: Generate vectors and push to Chroma DB
    print(f"Embedding chunks and storing in Chroma DB at {CHROMA_DB_DIR}...")
    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR,
        collection_name=COLLECTION_NAME
    )

    # Persist the database to disk so the FastAPI server can read it later
    vector_db.persist()

    print("Ingestion complete! The database is fully populated and ready for semantic search.")

if __name__ == "__main__":
    main()