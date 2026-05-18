const BASE_URL = "http://127.0.0.1:8000";

// ─── Key Derivation ───────────────────────────────────────
export async function deriveKey(password: string): Promise<CryptoKey> {
  const encoder = new TextEncoder();
  const keyMaterial = await window.crypto.subtle.importKey(
    "raw",
    encoder.encode(password),
    "PBKDF2",
    false,
    ["deriveKey"]
  );
  return window.crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: encoder.encode("fixed-salt-hackathon"),
      iterations: 100000,
      hash: "SHA-256",
    },
    keyMaterial,
    { name: "HMAC", hash: "SHA-256", length: 256 },
    false,
    ["sign"]
  );
}

// ─── Trigram Extraction ───────────────────────────────────
function extractTrigrams(text: string): string[] {
  const words = text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .split(/\s+/);
  const trigrams = new Set<string>();
  for (const word of words) {
    const w = word.length < 3 ? word.padEnd(3, "_") : word;
    for (let i = 0; i <= w.length - 3; i++) {
      trigrams.add(w.slice(i, i + 3));
    }
  }
  return [...trigrams];
}

// ─── Trapdoor Generation ──────────────────────────────────
async function generateTrapdoor(
  key: CryptoKey,
  trigram: string
): Promise<string> {
  const encoder = new TextEncoder();
  const sig = await window.crypto.subtle.sign(
    "HMAC",
    key,
    encoder.encode(trigram)
  );
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// ─── Get Noisy Embedding from Backend ────────────────────
async function getNoisyEmbedding(text: string): Promise<number[]> {
  const response = await fetch(`${BASE_URL}/embed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await response.json();
  return data.noisy_embedding;
}

// ─── Search ───────────────────────────────────────────────
export async function searchDocuments(query: string, key: CryptoKey) {
  // Step 1 — generate trapdoors in browser (query never sent raw)
  const trigrams = extractTrigrams(query);
  const trapdoors = await Promise.all(
    trigrams.map((t) => generateTrapdoor(key, t))
  );

  // Step 2 — get noisy query embedding from /embed endpoint
  const noisyQueryEmbedding = await getNoisyEmbedding(query);

  // Step 3 — send trapdoors + noisy embedding (never raw query)
  const response = await fetch(`${BASE_URL}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      trapdoor_tokens: trapdoors,
      noisy_query_embedding: noisyQueryEmbedding,
    }),
  });

  return response.json();
}

// ─── Upload ───────────────────────────────────────────────
export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });
  return response.json();
}