import numpy as np

from rag.vector_store import embedding_model


def blended_turn_accuracy(user_message: str, assistant_message: str) -> float:
    """
    Combine a simple substring heuristic with cosine similarity of sentence embeddings.
    Maps to [0, 1] for logging and adaptive difficulty.
    """
    u = (user_message or "").strip()
    a = (assistant_message or "").strip()
    if not u or not a:
        return 0.5

    heuristic = 1.0 if u.lower() in a.lower() else 0.5

    e1 = embedding_model.encode(u, convert_to_numpy=True)
    e2 = embedding_model.encode(a, convert_to_numpy=True)
    n1 = np.linalg.norm(e1) + 1e-9
    n2 = np.linalg.norm(e2) + 1e-9
    sim = float(np.dot(e1, e2) / (n1 * n2))
    semantic_01 = (sim + 1.0) / 2.0

    score = 0.35 * heuristic + 0.65 * semantic_01
    return max(0.0, min(1.0, score))
