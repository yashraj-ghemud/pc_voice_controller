"""
memory.py — Vector Database Conversation Memory for Fisira
Uses ChromaDB (local, persistent) + Gemini Embeddings (models/embedding-001)
to store past conversations and retrieve relevant context.
"""

import os
import time
import chromadb
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv("env.env", override=True)
load_dotenv(override=True)

# --- Config ---
CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
COLLECTION_NAME = "fisira_memory"
EMBEDDING_MODEL = "models/text-embedding-004"
MAX_RESULTS = 3  # How many past conversations to retrieve

# --- Gemini client for embeddings ---
_embed_client = None

def _get_embed_client():
    
    """Get or create a Gemini client for embeddings."""
    global _embed_client
    if _embed_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            _embed_client = genai.Client(api_key=api_key)
    return _embed_client


def _get_embedding(text: str) -> list[float] | None:
    """Generate embedding for a text using Gemini embedding model."""
    client = _get_embed_client()
    if not client:
        return None
    try:
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"⚠️ [Memory] Embedding error: {e}")
        return None


# --- ChromaDB Setup ---
_chroma_client = None
_collection = None

def _get_collection():
    """Get or create the ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        try:
            _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            _collection = _chroma_client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}  # cosine similarity
            )
            count = _collection.count()
            print(f"✅ [Memory] ChromaDB loaded — {count} memories stored at {CHROMA_DB_PATH}")
        except Exception as e:
            print(f"❌ [Memory] ChromaDB init failed: {e}")
            _collection = None
    return _collection


def save_conversation(user_msg: str, assistant_reply: str) -> bool:
    """
    Save a user+assistant exchange to ChromaDB.
    The document text is the combined exchange.
    Embedding is generated from the user message (for search relevance).
    """
    collection = _get_collection()
    if collection is None:
        return False

    # Create a combined document
    doc_text = f"User: {user_msg}\nFisira: {assistant_reply}"

    # Generate embedding from user message (better for search)
    embedding = _get_embedding(user_msg)
    if embedding is None:
        # Fallback: let ChromaDB use its default embedding (slower)
        print("⚠️ [Memory] Using fallback embedding")
        try:
            collection.add(
                documents=[doc_text],
                ids=[f"chat_{int(time.time() * 1000)}"],
                metadatas=[{
                    "timestamp": str(int(time.time())),
                    "user_msg": user_msg[:500],  # truncate for metadata
                }]
            )
            return True
        except Exception as e:
            print(f"❌ [Memory] Save failed (fallback): {e}")
            return False

    try:
        collection.add(
            documents=[doc_text],
            embeddings=[embedding],
            ids=[f"chat_{int(time.time() * 1000)}"],
            metadatas=[{
                "timestamp": str(int(time.time())),
                "user_msg": user_msg[:500],
            }]
        )
        return True
    except Exception as e:
        print(f"❌ [Memory] Save failed: {e}")
        return False


def get_relevant_context(query: str, top_k: int = MAX_RESULTS) -> str:
    """
    Search ChromaDB for past conversations relevant to the current query.
    Returns a formatted string of relevant past exchanges, or empty string.
    """
    collection = _get_collection()
    if collection is None or collection.count() == 0:
        return ""

    # Generate embedding for the query
    embedding = _get_embedding(query)
    if embedding is None:
        return ""

    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "distances"]
        )

        if not results or not results["documents"] or not results["documents"][0]:
            return ""

        # Filter by relevance (cosine distance < 0.7 means reasonably similar)
        relevant_docs = []
        for doc, distance in zip(results["documents"][0], results["distances"][0]):
            if distance < 0.7:  # cosine distance threshold
                relevant_docs.append(doc)

        if not relevant_docs:
            return ""

        # Format as context block
        context = "--- Past Conversations (for context) ---\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"\n[Memory {i}]:\n{doc}\n"
        context += "\n--- End Past Conversations ---"

        return context

    except Exception as e:
        print(f"⚠️ [Memory] Search failed: {e}")
        return ""


def get_memory_count() -> int:
    """Return the number of stored memories."""
    collection = _get_collection()
    return collection.count() if collection else 0


def clear_memory() -> bool:
    """Clear all stored memories."""
    global _collection
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        client.delete_collection(COLLECTION_NAME)
        _collection = None
        print("🗑️ [Memory] All memories cleared.")
        return True
    except Exception as e:
        print(f"❌ [Memory] Clear failed: {e}")
        return False


# Initialize on import (lazy — won't fail if chromadb not installed yet)
try:
    _get_collection()
except Exception:
    pass
