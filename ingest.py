"""
Data pipeline: ingest documents → chunk → embed → store in ChromaDB.
Run: python ingest.py
"""

import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

DOCUMENTS_DIR = Path("documents")
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "uic_cs_guide"

# Recursive chunking config for catalog docs
CHUNK_SIZE = 400
CHUNK_OVERLAP = 0

# Separators tried in order for recursive splitting
SEPARATORS = ["\n\n", "\n", ". ", " "]


# ── Recursive text splitter ────────────────────────────────────────────────

def recursive_split(text: str, separators: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Split text recursively on separators, targeting chunk_size characters."""
    sep = separators[0]
    remaining_seps = separators[1:]

    parts = text.split(sep) if sep else list(text)

    chunks = []
    current = ""
    for part in parts:
        candidate = (current + sep + part).lstrip(sep) if current else part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            # If this part alone exceeds chunk_size and we have more separators, recurse
            if len(part) > chunk_size and remaining_seps:
                sub_chunks = recursive_split(part, remaining_seps, chunk_size, overlap)
                chunks.extend(sub_chunks[:-1])
                current = sub_chunks[-1] if sub_chunks else ""
            else:
                current = part

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if c.strip()]


# ── Metadata extraction ────────────────────────────────────────────────────

def extract_metadata(text: str) -> dict:
    meta = {}
    for line in text.splitlines()[:10]:
        for key in ("SOURCE", "PROFESSOR", "OVERALL RATING", "COURSES TAUGHT", "TITLE", "SUBREDDIT"):
            if line.startswith(f"{key}:"):
                meta[key.lower().replace(" ", "_")] = line.split(f"{key}:", 1)[1].strip()
    return meta


# ── Document type helpers ──────────────────────────────────────────────────

def is_catalog(filename: str) -> bool:
    return filename.startswith("uic_")

def is_reddit(filename: str) -> bool:
    return filename.startswith("reddit_")

def is_rmp(filename: str) -> bool:
    return filename.startswith("rmp_")


# ── Chunkers ──────────────────────────────────────────────────────────────

def chunk_catalog(text: str, meta: dict) -> list[dict]:
    """Recursive chunking preserving section order for catalog docs."""
    lines = text.splitlines()
    # Skip header metadata lines (everything before the first blank line after line 3)
    body_start = 0
    for i, line in enumerate(lines):
        if i > 2 and line.strip() == "":
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:])

    raw_chunks = recursive_split(body, SEPARATORS, CHUNK_SIZE, CHUNK_OVERLAP)
    return [
        {"text": chunk, "metadata": {**meta, "chunk_type": "catalog"}}
        for chunk in raw_chunks
    ]


def chunk_reviews(text: str, meta: dict) -> list[dict]:
    """One chunk per review for RateMyProfessor files."""
    chunks = []
    review_pattern = re.compile(r"^REVIEW \|", re.MULTILINE)
    parts = review_pattern.split(text)
    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        inline_meta_line = lines[0].strip()
        review_body = "\n".join(lines[1:]).strip()

        review_meta = {**meta, "chunk_type": "review"}
        for field in inline_meta_line.split("|"):
            field = field.strip()
            if ":" in field:
                k, v = field.split(":", 1)
                review_meta[k.strip().lower().replace(" ", "_")] = v.strip()

        professor = meta.get("professor", "")
        chunk_text = f"[Professor: {professor}] [{inline_meta_line}]\n{review_body}"
        if chunk_text.strip():
            chunks.append({"text": chunk_text, "metadata": review_meta})
    return chunks


def chunk_reddit(text: str, meta: dict) -> list[dict]:
    """One chunk per post/comment for Reddit files."""
    chunks = []
    comment_pattern = re.compile(r"^(POST:|COMMENT \|)", re.MULTILINE)
    parts = comment_pattern.split(text)

    i = 1
    while i < len(parts):
        marker = parts[i].strip()  # "POST:" or "COMMENT |"
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        i += 2

        if not body:
            continue

        if marker == "POST:":
            chunk_text = f"[Reddit {meta.get('subreddit', '')} - Original Post | {meta.get('title', '')}]\n{body}"
            chunk_meta = {**meta, "chunk_type": "reddit_post"}
        else:
            # marker is "COMMENT |", body starts with "u/username..."
            chunk_text = f"[Reddit {meta.get('subreddit', '')} - Comment | {meta.get('title', '')}]\n{body}"
            chunk_meta = {**meta, "chunk_type": "reddit_comment"}

        chunks.append({"text": chunk_text, "metadata": chunk_meta})
    return chunks


# ── Main pipeline ──────────────────────────────────────────────────────────

def chunk_document(filename: str, text: str) -> list[dict]:
    meta = extract_metadata(text)
    meta["filename"] = filename

    if is_catalog(filename):
        return chunk_catalog(text, meta)
    elif is_rmp(filename):
        return chunk_reviews(text, meta)
    elif is_reddit(filename):
        return chunk_reddit(text, meta)
    return []


def build_index(chunks: list[dict]):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
    print(f"Stored {len(texts)} chunks in ChromaDB collection '{COLLECTION_NAME}'.")


def main():
    docs = list(DOCUMENTS_DIR.glob("*.txt"))
    print(f"Loaded {len(docs)} documents.")

    all_chunks = []
    for path in docs:
        text = path.read_text(encoding="utf-8")
        chunks = chunk_document(path.name, text)
        print(f"  {path.name}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"Total chunks: {len(all_chunks)}")
    build_index(all_chunks)


if __name__ == "__main__":
    main()
