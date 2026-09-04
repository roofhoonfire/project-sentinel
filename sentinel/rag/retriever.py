from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from sentinel.rag.ingest import (
    DocumentChunk,
    load_knowledge_chunks,
)


@dataclass
class RetrievalResult:
    source: str
    chunk_id: int
    score: float
    text: str


class KnowledgeRetriever:
    def __init__(
        self,
        knowledge_dir: str | Path,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.knowledge_dir = Path(knowledge_dir).resolve()

        print("[RAG] Loading embedding model...")
        self.model = SentenceTransformer(model_name)

        self.chunks: list[DocumentChunk] = (
            load_knowledge_chunks(self.knowledge_dir)
        )

        if not self.chunks:
            raise RuntimeError(
                f"No knowledge chunks found in {self.knowledge_dir}"
            )

        texts = [
            chunk.text
            for chunk in self.chunks
        ]

        print(
            f"[RAG] Embedding {len(texts)} knowledge chunks..."
        )

        # normalize_embeddings=True:
        # 각 embedding vector의 길이를 1로 만든다.
        self.embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        print(
            f"[RAG] Ready: matrix shape = {self.embeddings.shape}"
        )

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[RetrievalResult]:

        if not query.strip():
            return []

        query_vector = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        # 핵심:
        #
        # (N, 384) @ (384,)
        #
        # normalized vector이므로
        # inner product == cosine similarity
        scores = self.embeddings @ query_vector

        top_k = min(top_k, len(self.chunks))

        indices = np.argsort(scores)[::-1][:top_k]

        results = []

        for index in indices:
            chunk = self.chunks[index]

            results.append(
                RetrievalResult(
                    source=chunk.source,
                    chunk_id=chunk.chunk_id,
                    score=float(scores[index]),
                    text=chunk.text,
                )
            )

        return results
