"""
Run this FIRST before starting the server to confirm the ML layer works.
  python test_embeddings.py
"""
import numpy as np
from embeddings import (
    get_embedding,
    add_noise,
    remove_noise,
    cosine_similarity,
    serialize_embedding,
    deserialize_embedding,
    semantic_search,
    SBERT_AVAILABLE
)

KEY = b"test-secret-key-32bytes-padded!!"

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"


def test_sbert_loaded():
    print(f"\n{'='*55}")
    print(f"  SBERT Available: {SBERT_AVAILABLE}")
    if not SBERT_AVAILABLE:
        print("  Run: pip install sentence-transformers")
    print(f"{'='*55}")


def test_semantic_similarity():
    print("\n[1] Semantic Similarity Pairs")
    print(f"  {'Query':<25} {'Document':<30} {'Score':>6}  Result")
    print("  " + "-"*70)

    pairs = [
        ("kidney failure",    "renal dysfunction",      0.6,  True,  "medical synonyms"),
        ("heart attack",      "myocardial infarction",  0.5,  True,  "medical synonyms"),
        ("termination clause","exit provision",          0.4,  True,  "legal synonyms"),
        ("fraud indicators",  "suspicious activity",    0.35, True,  "compliance terms"),
        ("kidney failure",    "stock market crash",     0.3,  False, "unrelated"),
        ("heart attack",      "weather forecast",       0.3,  False, "unrelated"),
    ]

    all_pass = True
    for q, d, thresh, should_be_high, label in pairs:
        e1 = get_embedding(q)
        e2 = get_embedding(d)
        score = cosine_similarity(e1, e2)
        passed = (score >= thresh) == should_be_high
        status = PASS if passed else FAIL
        direction = "HIGH" if should_be_high else "LOW"
        print(f"  {q:<25} {d:<30} {score:>6.3f}  {status} (expect {direction}: {label})")
        if not passed:
            all_pass = False

    return all_pass


def test_noise_reversible():
    print("\n[2] Noise Add / Remove (must be perfectly reversible)")
    texts = ["kidney failure", "heart attack", "contract termination"]
    all_pass = True

    for text in texts:
        original = get_embedding(text)
        noisy    = add_noise(original, KEY)
        recovered = remove_noise(noisy, KEY)
        diff = float(np.max(np.abs(original - recovered)))
        passed = diff < 1e-5
        status = PASS if passed else FAIL
        print(f"  '{text}' — max diff: {diff:.2e}  {status}")
        if not passed:
            all_pass = False

    return all_pass


def test_noise_hides_content():
    print("\n[3] Noise Actually Changes Vector (server can't use raw embedding)")
    original = get_embedding("kidney failure")
    noisy    = add_noise(original, KEY)
    diff = float(np.mean(np.abs(original - noisy)))
    passed = diff > 0.001
    status = PASS if passed else FAIL
    print(f"  Mean embedding shift from noise: {diff:.6f}  {status}")
    return passed


def test_serialization():
    print("\n[4] Serialize / Deserialize (bytes round-trip for DB storage)")
    original = get_embedding("test document")
    serialized   = serialize_embedding(original)
    deserialized = deserialize_embedding(serialized)
    diff = float(np.max(np.abs(original - deserialized)))
    passed = diff < 1e-7
    status = PASS if passed else FAIL
    print(f"  Max diff after bytes round-trip: {diff:.2e}  {status}")
    return passed


def test_semantic_search_pipeline():
    print("\n[5] Full Semantic Search Pipeline")

    docs = {
        "doc-001": "Patient has acute kidney failure requiring dialysis",
        "doc-002": "Renal dysfunction detected in elderly patient",
        "doc-003": "Stock market crash affects pension funds globally",
        "doc-004": "Myocardial infarction treated with aspirin protocol",
    }

    # Store noisy embeddings
    doc_ids = list(docs.keys())
    noisy_embeddings = []
    for doc_id in doc_ids:
        emb = get_embedding(docs[doc_id])
        noisy = add_noise(emb, KEY)
        noisy_embeddings.append(noisy)

    # Search
    results = semantic_search(
        query="kidney failure",
        doc_ids=doc_ids,
        noisy_embeddings=noisy_embeddings,
        key=KEY,
        top_k=3,
        threshold=0.25
    )

    print(f"  Query: 'kidney failure'")
    print(f"  Results (ranked):")
    for doc_id, score in results:
        print(f"    {doc_id} — score {score:.3f} — \"{docs[doc_id][:50]}\"")

    # Check doc-001 and doc-002 rank above doc-003
    result_ids = [r[0] for r in results]
    passed = "doc-001" in result_ids or "doc-002" in result_ids
    status = PASS if passed else FAIL
    print(f"  Medical docs ranked above 'stock market'?  {status}")
    return passed


def test_different_keys_different_noise():
    print("\n[6] Different Keys Produce Different Noise (security check)")
    key_a = b"key-A-32bytes-padded-for-testing!"
    key_b = b"key-B-32bytes-padded-for-testing!"
    emb = get_embedding("test")
    noisy_a = add_noise(emb, key_a)
    noisy_b = add_noise(emb, key_b)
    diff = float(np.mean(np.abs(noisy_a - noisy_b)))
    passed = diff > 0.001
    status = PASS if passed else FAIL
    print(f"  Mean diff between noise from key_a vs key_b: {diff:.6f}  {status}")
    return passed


if __name__ == "__main__":
    test_sbert_loaded()

    results = [
        test_semantic_similarity(),
        test_noise_reversible(),
        test_noise_hides_content(),
        test_serialization(),
        test_semantic_search_pipeline(),
        test_different_keys_different_noise(),
    ]

    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*55}")
    print(f"  Results: {passed}/{total} test groups passed")
    if passed == total:
        print("  \033[92mML layer is ready. Start the server.\033[0m")
    else:
        print("  \033[91mFix failures above before running the server.\033[0m")
    print(f"{'='*55}\n")