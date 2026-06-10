"""
Retrieval layer: hybrid vector + BM25 search over the ChromaDB collection.

Pipeline stage 4 (from planning.md architecture diagram):
  Embedding store (ChromaDB, all-MiniLM-L6-v2)
      └─ 4a. Vector search  (cosine similarity)
      └─ 4b. Keyword search (BM25)
           └─ Merge & re-rank → top-k results → Generation

Usage:
    from retrieve import build_retriever, retrieve
    retriever = build_retriever()
    results = retrieve(retriever, "Who is the best professor for CS 361?")
"""

import re
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "uic_cs_guide"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def build_retriever() -> dict:
    """
    Load the ChromaDB collection and build a BM25 index over all stored chunks.
    Returns a retriever dict holding both indexes and the embedding model.
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    all_data = collection.get(include=["documents", "metadatas"])
    documents = all_data["documents"]
    metadatas = all_data["metadatas"]
    ids = all_data["ids"]

    # BM25 index over tokenized documents
    tokenized = [_tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized)

    model = SentenceTransformer(EMBED_MODEL)

    return {
        "collection": collection,
        "model": model,
        "bm25": bm25,
        "documents": documents,
        "metadatas": metadatas,
        "ids": ids,
    }


def retrieve(retriever: dict, query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Hybrid retrieval: vector search + BM25, merged by Reciprocal Rank Fusion.
    Returns a list of top_k dicts with keys: text, metadata, score.
    """
    collection = retriever["collection"]
    model = retriever["model"]
    bm25 = retriever["bm25"]
    documents = retriever["documents"]
    metadatas = retriever["metadatas"]
    ids = retriever["ids"]
    n = len(documents)

    # ── 4a. Vector search ──────────────────────────────────────────────────
    query_embedding = model.encode(query).tolist()
    vec_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k * 3, n),
        include=["documents", "metadatas", "distances"],
    )
    vec_ids = vec_results["ids"][0]
    # Map id → rank (0-based, lower = better)
    vec_ranks = {doc_id: rank for rank, doc_id in enumerate(vec_ids)}

    # ── 4b. BM25 keyword search ────────────────────────────────────────────
    tokenized_query = _tokenize(query)
    bm25_scores = bm25.get_scores(tokenized_query)
    bm25_ranked = sorted(
        range(n), key=lambda i: bm25_scores[i], reverse=True
    )[: top_k * 3]
    # Map id → rank
    bm25_ranks = {ids[i]: rank for rank, i in enumerate(bm25_ranked)}

    # ── Merge: Reciprocal Rank Fusion (RRF) ───────────────────────────────
    # RRF score = 1/(k+rank_vec) + 1/(k+rank_bm25), k=60 is standard
    k = 60
    candidate_ids = set(vec_ranks) | set(bm25_ranks)
    rrf_scores = {}
    for doc_id in candidate_ids:
        vec_r = vec_ranks.get(doc_id, top_k * 3)
        bm25_r = bm25_ranks.get(doc_id, top_k * 3)
        rrf_scores[doc_id] = 1 / (k + vec_r) + 1 / (k + bm25_r)

    top_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]

    # Build result list preserving original document text and metadata
    id_to_index = {doc_id: i for i, doc_id in enumerate(ids)}
    results = []
    for doc_id in top_ids:
        idx = id_to_index[doc_id]
        results.append({
            "text": documents[idx],
            "metadata": metadatas[idx],
            "score": rrf_scores[doc_id],
        })

    return results


if __name__ == "__main__":
    # Quick smoke test
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "best professor for CS 361"
    print(f"Query: {query}\n")
    retriever = build_retriever()
    results = retrieve(retriever, query)
    for i, r in enumerate(results):
        meta = r["metadata"]
        print(f"[{i+1}] score={r['score']:.4f} | type={meta['chunk_type']} | file={meta['filename']}")
        print(r["text"][:300])
        print()
