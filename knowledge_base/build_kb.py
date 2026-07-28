# ============================================================
# KNOWLEDGE BASE BUILDER
# ============================================================
# This script builds the vector database that MedAgent's RAG
# agent will search. It only needs to run ONCE (or whenever
# the source articles are updated).
#
# WHAT IT DOES:
#   1. Reads all the scraped medical articles
#   2. Splits each article into small chunks (~500 chars)
#   3. Converts each chunk into a number-vector (embedding)
#   4. Stores the chunks + vectors in ChromaDB
#
# WHY EMBEDDINGS?
#   Vectors let us search by MEANING, not exact keywords.
#   "high liver enzymes" and "elevated ALT" produce similar
#   vectors even though the words don't overlap. This is the
#   key insight of modern semantic search.
# ============================================================

import os
import chromadb
from sentence_transformers import SentenceTransformer

# Where the scraped articles live
SOURCES_DIR = "knowledge_base/sources"

# Where to store the vector database (a local folder)
DB_DIR = "knowledge_base/chroma_db"

# Size of each chunk in characters. Small enough to be focused,
# large enough to contain useful context.
CHUNK_SIZE = 500

# How much chunks should overlap. Overlap prevents important
# ideas from being split across chunk boundaries.
CHUNK_OVERLAP = 100


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split a long text into smaller overlapping chunks."""
    chunks = []
    start = 0

    while start < len(text):
        # Take a slice of chunk_size characters
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at a sensible boundary (sentence end)
        # instead of mid-word. Only do this if we're not at
        # the very end of the text.
        if end < len(text):
            # Find the last sentence-ending or newline in this chunk
            last_break = max(chunk.rfind(". "), chunk.rfind("\n"))
            if last_break > chunk_size // 2:
                # Only use it if it's past the halfway mark
                chunk = chunk[:last_break + 1]
                end = start + last_break + 1

        chunks.append(chunk.strip())

        # Move forward, but overlap with the previous chunk
        start = end - overlap

    # Remove any tiny chunks (less than 50 chars = probably junk)
    return [c for c in chunks if len(c) > 50]


def main():
    print("Building MedAgent knowledge base...\n")

    # STEP 1: Load the embedding model.
    # 'all-MiniLM-L6-v2' is a lightweight model that runs
    # locally on CPU (no GPU needed) and produces 384-dimensional
    # vectors. It's a widely-used, well-tested choice for RAG.
    # First run will download ~90MB (only happens once).
    print("Loading embedding model (first run downloads ~90MB)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("  Model loaded.\n")

    # STEP 2: Set up ChromaDB.
    # PersistentClient means the database is saved to disk.
    # No external database server needed - it lives in a
    # local folder.
    client = chromadb.PersistentClient(path=DB_DIR)

    # Delete any existing collection so we start fresh.
    # This is safe to do because we can always rebuild.
    try:
        client.delete_collection("medical_knowledge")
        print("  Deleted existing collection.")
    except Exception:
        pass  # Collection didn't exist yet - fine

    # Create a new collection to hold our chunks + embeddings
    collection = client.create_collection(
        name="medical_knowledge",
        metadata={"description": "MedlinePlus articles about blood tests"}
    )
    print("  Collection created.\n")

    # STEP 3: Process each source file
    all_chunks = []
    all_metadatas = []
    all_ids = []

    files = [f for f in os.listdir(SOURCES_DIR) if f.endswith(".txt")]
    print(f"Found {len(files)} source articles\n")

    for filename in sorted(files):
        test_name = filename.replace(".txt", "")
        filepath = os.path.join(SOURCES_DIR, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Split the article into chunks
        chunks = chunk_text(content)
        print(f"  {test_name}: {len(chunks)} chunks")

        # Store each chunk with metadata linking it to its test
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "test": test_name,
                "source": "MedlinePlus",
                "chunk_index": i,
            })
            # Give each chunk a unique ID
            all_ids.append(f"{test_name}_{i}")

    # STEP 4: Generate embeddings for all chunks at once (faster
    # than doing them one at a time)
    print(f"\nEmbedding {len(all_chunks)} chunks...")
    embeddings = model.encode(all_chunks, show_progress_bar=True).tolist()

    # STEP 5: Add everything to ChromaDB in one batch
    collection.add(
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas,
        ids=all_ids,
    )

    print(f"\nKnowledge base built successfully!")
    print(f"   Total chunks stored: {collection.count()}")
    print(f"   Database location: {DB_DIR}")

    # BONUS: Test a quick search to prove it works
    print("\n--- Testing the knowledge base ---")
    test_query = "high alt liver enzymes what does it mean"
    query_embedding = model.encode(test_query).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=2)

    print(f"Query: '{test_query}'")
    print(f"Top match: {results['documents'][0][0][:200]}...")


if __name__ == "__main__":
    main()