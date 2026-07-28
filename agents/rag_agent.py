# ============================================================
# RAG AGENT (RETRIEVAL AGENT)
# ============================================================
# This is the THIRD agent in the MedAgent pipeline, sitting
# between the Analysis Agent and the Report Writer Agent.
#
# Its job: given a list of abnormal test results, retrieve
# the most relevant medical context from the knowledge base
# to help Claude write an accurate, grounded explanation.
#
# WHY THIS EXISTS:
#   Without RAG, Claude relies on its training knowledge alone,
#   which may be outdated or subtly wrong. With RAG, Claude
#   receives fresh, trusted content from MedlinePlus at the
#   moment of generation - which is far more reliable and
#   traceable.
#
# HOW IT WORKS (semantic search):
#   1. Take the test name + status as a "query"
#   2. Convert the query into a vector using the same
#      embedding model used to build the KB
#   3. Find the top-K most similar chunks in ChromaDB
#   4. Return those chunks as context for the LLM
# ============================================================

import os
import chromadb
from sentence_transformers import SentenceTransformer

# Path to the vector database built by build_kb.py
DB_DIR = "knowledge_base/chroma_db"

# Both must match the model used in build_kb.py.
# You can't search a database built with one model using
# embeddings from a different model - the vectors would be
# in different "spaces" and matches would be meaningless.
MODEL_NAME = "all-MiniLM-L6-v2"

# Global variables so we only load the model once per program
# run (loading takes a couple of seconds). This is called
# "lazy initialisation" - only load when actually needed.
_model = None
_collection = None


def _init():
    """Load the embedding model and connect to ChromaDB.
    Only runs once per program execution."""
    global _model, _collection

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    if _collection is None:
        client = chromadb.PersistentClient(path=DB_DIR)
        _collection = client.get_collection("medical_knowledge")


def _has_test(test_name):
    """Check if we have KB entries for this specific test name.
    Used to decide whether to filter by test or search all chunks."""
    _init()
    try:
        results = _collection.get(where={"test": test_name}, limit=1)
        return len(results["ids"]) > 0
    except Exception:
        return False


def retrieve_context_for_test(test_name, status, top_k=3):
    """
    Retrieve the most relevant chunks for a specific test result.

    Args:
        test_name: e.g. "alt", "haemoglobin"
        status: "HIGH", "LOW", or "NORMAL"
        top_k: how many chunks to return

    Returns:
        A list of chunk texts, ordered by relevance (best first).
    """
    _init()

    # Build a query that captures both the test AND the direction.
    # Including "high" or "low" in the query helps semantic search
    # find chunks discussing that specific abnormality direction.
    query = f"{test_name} {status.lower()} what does it mean causes"

    # Convert the query to a vector using the same model
    query_embedding = _model.encode(query).tolist()

    # Search the database.
    # If we have KB entries for this specific test, filter by it
    # to get the most relevant chunks. Otherwise search everything.
    if _has_test(test_name):
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"test": test_name},
        )
    else:
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

    # Extract just the text of each retrieved chunk.
    # results["documents"] is a list of lists (one list per query),
    # so we take [0] to get the results for our single query.
    if results and results["documents"]:
        return results["documents"][0]

    return []


def retrieve_context_for_all_abnormals(abnormal_results):
    """
    Retrieve context for every abnormal test in the results.

    Args:
        abnormal_results: list of dicts with 'test' and 'status' keys

    Returns:
        A dict mapping test names to their retrieved context text.
    """
    context_map = {}

    for r in abnormal_results:
        test = r.get("test", "")
        status = r.get("status", "")

        # Retrieve top-2 chunks per test (enough for context,
        # not so much that it bloats the LLM prompt)
        chunks = retrieve_context_for_test(test, status, top_k=2)

        if chunks:
            # Join the retrieved chunks with a clear separator
            context_map[test] = "\n\n---\n\n".join(chunks)

    return context_map


# ============================================================
# Quick manual test when run directly
# ============================================================
# Run this file directly with: python agents/rag_agent.py
# to check the RAG agent works before integrating.
# ============================================================

if __name__ == "__main__":
    print("Testing RAG Agent...\n")

    # Simulate what the Analysis Agent would send us
    test_abnormals = [
        {"test": "alt", "status": "HIGH", "value": "72"},
        {"test": "haemoglobin", "status": "LOW", "value": "11.2"},
        {"test": "glucose", "status": "HIGH", "value": "115"},
    ]

    context = retrieve_context_for_all_abnormals(test_abnormals)

    for test, content in context.items():
        print("=" * 60)
        print(f"TEST: {test}")
        print("=" * 60)
        # Only show first 300 chars per test for readability
        print(content[:300] + "...")
        print()