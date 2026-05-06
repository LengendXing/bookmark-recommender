import json
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import select

import chromadb
import numpy as np
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.database import Session, get_db
from app.models.bookmark import Bookmark
from app.models.model_version import ModelVersion

settings = get_settings()

_MODEL_NAME = "all-MiniLM-L6-v2"
_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def get_chroma_client():
    return chromadb.PersistentClient(
        path=settings.CHROMA_DB_PATH,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def encode(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True).tolist()


def encode_single(text: str) -> list[float]:
    return encode([text])[0]


def _build_doc_text(bm: Bookmark) -> str:
    tags = json.loads(bm.tags) if isinstance(bm.tags, str) else (bm.tags or [])
    parts = [
        bm.title,
        bm.description,
        bm.category,
        " ".join(tags),
        bm.generated_title or "",
        bm.generated_description or "",
        (bm.page_text or "")[:1000],
    ]
    return " ".join(filter(None, parts))


def train_index():
    """Full re-index: read all bookmarks from SQLite, encode, upsert to ChromaDB."""
    from app.core.database import engine

    client = get_chroma_client()
    collection_name = "br_bookmarks"

    if collection_name in [c.name for c in client.list_collections()]:
        client.delete_collection(collection_name)
    collection = client.create_collection(collection_name)

    db = Session(bind=engine)
    try:
        result = db.execute(select(Bookmark).where(Bookmark.title != ""))
        bookmarks = result.scalars().all()
    finally:
        db.close()

    if not bookmarks:
        return

    texts = [_build_doc_text(bm) for bm in bookmarks]
    embeddings = encode(texts)

    ids = [str(bm.id) for bm in bookmarks]
    metadatas = [
        {
            "title": bm.title,
            "url": bm.url,
            "description": bm.description or "",
            "category": bm.category or "",
            "tags": bm.tags,
            "user_id": bm.user_id,
        }
        for bm in bookmarks
    ]

    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    db = Session(bind=engine)
    try:
        mv = ModelVersion(
            model_name=_MODEL_NAME,
            version="0.2.0",
            framework="sentence-transformers",
            dataset_size=len(bookmarks),
            status="trained",
            training_params=json.dumps({"n_bookmarks": len(bookmarks)}),
        )
        db.add(mv)
        db.commit()
    finally:
        db.close()


def semantic_search(query: str, candidate_texts: list[str], top_k: int = 20) -> tuple[list[int], list[float]]:
    """Compute cosine similarity between query and candidates. Returns (indices, scores)."""
    if not candidate_texts:
        return [], []

    model = _get_model()
    query_emb = model.encode([query], normalize_embeddings=True)
    doc_embs = model.encode(candidate_texts, normalize_embeddings=True)

    scores = np.dot(doc_embs, query_emb.T).flatten()
    if len(scores) == 0:
        return [], []

    k = min(top_k, len(scores))
    top_indices = np.argsort(scores)[-k:][::-1]
    top_scores = scores[top_indices]
    return top_indices.tolist(), top_scores.tolist()


def recommend(query: str, limit: int = 10) -> list[dict]:
    client = get_chroma_client()
    collection_name = "br_bookmarks"

    if collection_name not in [c.name for c in client.list_collections()]:
        return []

    collection = client.get_collection(collection_name)
    query_emb = encode_single(query)

    results = collection.query(query_embeddings=[query_emb], n_results=limit, include=["metadatas", "distances"])

    if not results["ids"] or not results["ids"][0]:
        return []

    items = []
    for idx, doc_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][idx]
        distance = results["distances"][0][idx]
        tags = json.loads(meta.get("tags", "[]")) if isinstance(meta.get("tags"), str) else []
        items.append({
            "id": int(doc_id),
            "title": meta.get("title", ""),
            "url": meta.get("url", ""),
            "description": meta.get("description", ""),
            "category": meta.get("category", ""),
            "score": round(1 - distance, 4),
            "tags": tags if isinstance(tags, list) else [],
        })

    return items
