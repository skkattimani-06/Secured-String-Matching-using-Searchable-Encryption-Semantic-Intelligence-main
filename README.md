Secured String Matching using Searchable Encryption + Semantic Intelligence
---
What is This Project?
A system that lets you search through encrypted documents stored on a cloud server — without the server ever knowing what you searched or what the documents contain.
Most systems force you to choose between encryption and search. We built a system that gives you both.
---
Features
Exact Keyword Search — Find documents containing the exact word you searched
Substring Search — Partial words still find the right document (`dialy` finds `dialysis`)
Fuzzy Search — Typos are handled automatically (`kidny failur` finds `kidney failure`)
Semantic Search — Search by meaning, not just words (`heart attack` finds `myocardial infarction`)
Privacy Guaranteed — The server never sees your query, only encrypted trapdoor tokens
Input Validation — Empty queries and uploads are handled gracefully
---
How It Works
Upload Flow
```
User selects document
        ↓
Document encrypted with AES-256-GCM in browser
        ↓
Trigrams extracted → HMAC-SHA256 trapdoors generated
        ↓
Sentence-BERT generates meaning vector → noise masked
        ↓
Only encrypted data sent to server
        ↓
Server stores ciphertext + trapdoor index + noisy vectors
```
Search Flow
```
User types query
        ↓
Browser breaks query into trigrams
        ↓
HMAC-SHA256 trapdoor tokens generated (query never sent)
        ↓
/embed endpoint generates noisy query embedding
        ↓
Server receives only: trapdoor tokens + noisy embedding
        ↓
Server matches tokens + computes cosine similarity
        ↓
Returns encrypted results → browser decrypts and displays
```
---
Tech Stack
Layer	Technology
Frontend	React + TypeScript + TailwindCSS
Backend	FastAPI (Python)
Encryption	AES-256-GCM + HMAC-SHA256 + PBKDF2
Semantic ML	Sentence-BERT (all-MiniLM-L6-v2)
Vector Privacy	Deterministic noise masking (NumPy)
Similarity Ranking	Cosine similarity
Database	PostgreSQL
---
Security Model
Tier 1 — Keyword Search (Cryptographically Secure)
Documents encrypted with AES-256-GCM
Search uses HMAC-SHA256 trapdoor tokens
Server learns only: access pattern and search pattern
Server learns nothing about: document content or query terms
Tier 2 — Semantic Search (Obfuscation-Based)
Embeddings masked with deterministic key-derived noise
Server sees only noisy float arrays
Prevents casual reconstruction of document meaning
Future upgrade: CKKS Homomorphic Encryption for formal proof
---

Setup and Running
Prerequisites
Python 3.9+
Node.js 18+
PostgreSQL
---
Backend Setup
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
# Make sure PostgreSQL is running and create a database named 'sse_db'
# Update connection string in database.py if needed

# Run the backend server
uvicorn main:app --reload
```
Backend runs at: `http://127.0.0.1:8000`
---
Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run the frontend
npm run dev
```
Frontend runs at: `http://localhost:5173`
---
Privacy Proof
Open browser DevTools → Network tab → search anything → click the `/search` request → Payload tab.
You will see:
```json
{
  "trapdoor_tokens": [
    "7f4e1b2a9c3d8e2f...",
    "3a9f2c8b1e4f7d9a..."
  ],
  "noisy_query_embedding": [0.23, -0.11, 0.87, ...]
}
```
The actual query word is never sent to the server.
---
