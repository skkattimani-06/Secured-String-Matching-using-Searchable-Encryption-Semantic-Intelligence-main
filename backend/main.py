from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import uuid
import numpy as np

from crypto import (
    derive_key,
    encrypt_document,
    decrypt_document
)

from embeddings import (
    get_embedding,
    add_noise,
    remove_noise,
    cosine_similarity
)

from database import engine, SessionLocal
from models import Base, Document

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MASTER_PASSWORD = "password123"
KEY = derive_key(MASTER_PASSWORD)

# -----------------------------
# Request Models
# -----------------------------

class SearchRequest(BaseModel):
    trapdoor_tokens: List[str]
    noisy_query_embedding: List[float]

class EmbedRequest(BaseModel):
    text: str

# -----------------------------
# Upload Endpoint
# -----------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        try:
            text_content = contents.decode("utf-8")
        except UnicodeDecodeError:
            text_content = contents.decode("latin-1")

        encrypted = encrypt_document(KEY, text_content)
        embedding = get_embedding(text_content)
        noisy_embedding = add_noise(embedding, KEY)

        db = SessionLocal()

        # Prevent duplicate uploads
        existing_docs = db.query(Document).all()
        for doc in existing_docs:
            existing_content = decrypt_document(KEY, doc.encrypted)
            if existing_content == text_content:
                db.close()
                return {
                    "message": "Document already exists, skipping duplicate.",
                    "filename": file.filename
                }

        doc = Document(
            id=str(uuid.uuid4()),
            encrypted=encrypted,
            embedding=noisy_embedding.astype(np.float32).tobytes()
        )
        db.add(doc)
        db.commit()
        db.close()

        return {
            "message": "Document encrypted and stored successfully.",
            "filename": file.filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Gibberish Detection
# -----------------------------

def looks_like_gibberish(text: str) -> bool:
    """
    Real English words have vowels.
    Gibberish like 'dgdhfthfhgf' has almost no vowels.
    Normal English has ~38% vowels.
    Gibberish typically has less than 10%.
    """
    text = text.lower().replace(" ", "")
    if len(text) == 0:
        return True
    vowels = sum(1 for c in text if c in "aeiou")
    vowel_ratio = vowels / len(text)
    return vowel_ratio < 0.10


# -----------------------------
# Embed Endpoint
# -----------------------------

@app.post("/embed")
def get_noisy_embedding(request: EmbedRequest):

    # If gibberish detected — return a negative vector
    if looks_like_gibberish(request.text):
        negative_vector = np.full(384, -0.5, dtype=np.float32)
        noisy = add_noise(negative_vector, KEY)
        return {"noisy_embedding": noisy.tolist()}

    # Normal query — return real embedding
    embedding = get_embedding(request.text)
    noisy = add_noise(embedding, KEY)
    return {"noisy_embedding": noisy.tolist()}


# -----------------------------
# Search Endpoint
# -----------------------------

@app.post("/search")
def search_documents(request: SearchRequest):

    if not request.trapdoor_tokens:
        raise HTTPException(
            status_code=400,
            detail="No trapdoor tokens provided"
        )

    db = SessionLocal()

    try:
        documents = db.query(Document).all()

        if not documents:
            return {"results": []}

        # Remove noise from query embedding
        query_embedding = np.array(
            request.noisy_query_embedding, dtype=np.float32
        )
        query_embedding = remove_noise(query_embedding, KEY)

        # Normalize query embedding
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm

        scored = []

        for doc in documents:
            # Get clean stored embedding
            stored_embedding = np.frombuffer(
                doc.embedding, dtype=np.float32
            ).copy()
            clean_embedding = remove_noise(stored_embedding, KEY)

            # Normalize stored embedding
            stored_norm = np.linalg.norm(clean_embedding)
            if stored_norm > 0:
                clean_embedding = clean_embedding / stored_norm

            # Real cosine similarity between query and document
            score = float(np.dot(query_embedding, clean_embedding))

            # Decrypt content for display
            decrypted = decrypt_document(KEY, doc.encrypted)

            scored.append({
                "doc_id": doc.id,
                "score": round(score, 4),
                "content": decrypted
            })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        # Return top 3 unique results
        seen = set()
        unique_results = []
        for r in scored:
            if r["content"] not in seen:
                seen.add(r["content"])
                unique_results.append(r)
            if len(unique_results) == 3:
                break

        return {"results": unique_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()


# -----------------------------
# Audit Endpoint
# -----------------------------

@app.get("/audit")
def audit():
    db = SessionLocal()
    try:
        documents = db.query(Document).all()

        audit_data = []
        for doc in documents:
            audit_data.append({
                "doc_id": doc.id,
                "stored_blob": str(doc.encrypted[:60]) + "...",
                "embedding_sample": str(
                    np.frombuffer(doc.embedding, dtype=np.float32)[:5].tolist()
                ) + "..."
            })

        return {
            "message": "This is everything the server stores. No plaintext.",
            "documents": audit_data
        }

    finally:
        db.close()