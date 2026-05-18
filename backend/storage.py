from typing import Dict, List
import numpy as np

DOCUMENTS: Dict[str, dict] = {}
INVERTED_INDEX: Dict[str, List[str]] = {}


def store_document(doc_id: str, encrypted: bytes, embedding: np.ndarray, trapdoors: List[str]):
    DOCUMENTS[doc_id] = {
        "encrypted": encrypted,
        "embedding": embedding
    }

    for trapdoor in trapdoors:
        if trapdoor not in INVERTED_INDEX:
            INVERTED_INDEX[trapdoor] = []
        INVERTED_INDEX[trapdoor].append(doc_id)


def get_all_documents():
    return DOCUMENTS


def get_matching_docs(trapdoors: List[str]):
    matched = set()

    for trapdoor in trapdoors:
        if trapdoor in INVERTED_INDEX:
            matched.update(INVERTED_INDEX[trapdoor])

    return list(matched)