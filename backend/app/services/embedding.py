import json
import os
from pathlib import Path
from typing import Optional

import chromadb
import numpy as np
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.database import async_session
from app.models.bookmark import Bookmark
from app.models.model_version import ModelVersion
from sqlalchemy import select

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


async def train_index():
    """Full re-index: read all bookmarks from SQLite, encode, upsert to ChromaDB."""
    client = get_chroma_client()
    collection_name = "br_bookmarks"

    if collection_name in [c.name for c in client.list_collections()]:
        client.delete_collection(collection_name)
    collection = client.create_collection(collection_name)

    async with async_session() as db:
        result = await db.execute(select(Bookmark).where(Bookmark.title != ""))
        bookmarks = result.scalars().all()

    if not bookmarks:
        return

    texts = [f"{bm.title} {bm.description} {bm.category}" for bm in bookmarks]
    embeddings = encode(texts)

    ids = [str(bm.id) for bm in bookmarks]
    metadatas = [
        {
            "title": bm.title,
            "url": bm.url,
            "category": bm.category,
            "tags": bm.tags,
            "user_id": bm.user_id,
        }
        for bm in bookmarks
    ]

    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    async with async_session() as db:
        mv = ModelVersion(
            model_name=_MODEL_NAME,
            version="0.1.0",
            framework="sentence-transformers",
            dataset_size=len(bookmarks),
            status="trained",
            training_params=json.dumps({"n_bookmarks": len(bookmarks)}),
        )
        db.add(mv)
        await db.commit()


async def recommend(query: str, limit: int = 10) -> list[dict]:
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
            "score": round(1 - distance, 4),
            "tags": tags if isinstance(tags, list) else [],
        })

    return items
