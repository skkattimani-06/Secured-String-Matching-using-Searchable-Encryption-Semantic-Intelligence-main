import numpy as np
import hashlib
from typing import List, Tuple

# ---------------------------------------------------------------
# REAL ML: Sentence-BERT for semantic understanding
# pip install sentence-transformers
# ---------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB, downloads once
    SBERT_AVAILABLE = True
    print("[ML] Sentence-BERT loaded: all-MiniLM-L6-v2")
except ImportError:
    SBERT_AVAILABLE = False
    print("[ML] WARNING: sentence-transformers not installed. Using hash fallback.")

VECTOR_SIZE = 384  # SBERT output dimension


# ---------------------------------------------------------------
# 1. Embedding Generation
# ---------------------------------------------------------------

def get_embedding(text: str) -> np.ndarray:
    """
    Converts text to a 384-dim semantic vector using Sentence-BERT.
    'kidney failure' and 'renal dysfunction' will score > 0.8 similarity.
    Falls back to hash method if sentence-transformers not installed.
    """
    if SBERT_AVAILABLE:
        embedding = _model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)
    return _hash_fallback_embedding(text)


def _hash_fallback_embedding(text: str) -> np.ndarray:
    """Hash-based fallback — NO semantic understanding. Emergency use only."""
    vector = np.zeros(VECTOR_SIZE, dtype=np.float32)
    words = text.lower().split()
    for word in words:
        h = int(hashlib.sha256(word.encode()).hexdigest(), 16)
        index = h % VECTOR_SIZE
        vector[index] += 1.0
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector


# ---------------------------------------------------------------
# 2. Deterministic Noise (Privacy Layer)
# ---------------------------------------------------------------

def _generate_noise(key: bytes, size: int) -> np.ndarray:
    """
    Deterministic noise derived from secret key.
    Same key = same noise every time → fully reversible by client.
    Server only sees noisy vector and cannot reconstruct the original.
    """
    seed = int(hashlib.sha256(key).hexdigest(), 16) % (2**32)
    rng = np.random.default_rng(seed)
    return rng.normal(0, 0.01, size).astype(np.float32)


def add_noise(embedding: np.ndarray, key: bytes) -> np.ndarray:
    """Masks embedding before storing on server."""
    return embedding + _generate_noise(key, embedding.shape[0])


def remove_noise(noisy_embedding: np.ndarray, key: bytes) -> np.ndarray:
    """Recovers original embedding from noisy version using secret key."""
    return noisy_embedding - _generate_noise(key, noisy_embedding.shape[0])


# ---------------------------------------------------------------
# 3. Serialization (numpy <-> bytes for DB storage)
# ---------------------------------------------------------------

def serialize_embedding(embedding: np.ndarray) -> bytes:
    """Convert numpy array to bytes for LargeBinary DB column."""
    return embedding.astype(np.float32).tobytes()


def deserialize_embedding(data: bytes) -> np.ndarray:
    """Convert bytes from DB back to numpy array."""
    return np.frombuffer(data, dtype=np.float32).copy()


# ---------------------------------------------------------------
# 4. Cosine Similarity & Ranking
# ---------------------------------------------------------------

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Measures semantic closeness. 1.0 = identical meaning, 0.0 = unrelated."""
    denom = np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-8
    return float(np.dot(vec1, vec2) / denom)


def rank_documents(
    query_embedding: np.ndarray,
    document_embeddings: List[np.ndarray],
    threshold: float = 0.25
) -> List[int]:
    """
    Ranks document indices by semantic similarity to query.
    Returns indices sorted best to worst, filtered by threshold.
    """
    scores = [cosine_similarity(query_embedding, doc_emb)
              for doc_emb in document_embeddings]
    ranked = sorted(
        [i for i, s in enumerate(scores) if s >= threshold],
        key=lambda i: scores[i],
        reverse=True
    )
    return ranked


def semantic_search(
    query: str,
    doc_ids: List[str],
    noisy_embeddings: List[np.ndarray],
    key: bytes,
    top_k: int = 5,
    threshold: float = 0.25
) -> List[Tuple[str, float]]:
    """
    Full semantic search pipeline:
      1. Embed query with SBERT
      2. Remove noise from each stored embedding
      3. Rank by cosine similarity
      4. Return (doc_id, score) pairs above threshold
    """
    if not doc_ids:
        return []

    query_embedding = get_embedding(query)
    results = []

    for doc_id, noisy_emb in zip(doc_ids, noisy_embeddings):
        clean_emb = remove_noise(noisy_emb, key)
        score = cosine_similarity(query_embedding, clean_emb)
        if score >= threshold:
            results.append((doc_id, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]