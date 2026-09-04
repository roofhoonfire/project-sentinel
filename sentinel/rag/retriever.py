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
        self.knowledge_dir = Path(
            knowledge_dir
        ).resolve()

        print(
            "[RAG] Loading embedding model..."
        )

        self.model = SentenceTransformer(
            model_name
        )

        self.chunks: list[
            DocumentChunk
        ] = []

        self.embeddings = np.empty(
            (
                0,
                self.model.get_sentence_embedding_dimension(),
            ),
            dtype=np.float32,
        )

        self.reload()

    def reload(self):
        """
        Reload Markdown knowledge and rebuild the embedding index.

        The embedding model itself is NOT reloaded.
        Only knowledge chunks and vectors are regenerated.
        """

        self.chunks = load_knowledge_chunks(
            self.knowledge_dir
        )

        print(
            f"[RAG] Embedding "
            f"{len(self.chunks)} knowledge chunks..."
        )

        if not self.chunks:
            self.embeddings = np.empty(
                (
                    0,
                    self.model.get_sentence_embedding_dimension(),
                ),
                dtype=np.float32,
            )

            print(
                "[RAG] Ready: no knowledge chunks"
            )
            return

        texts = [
            chunk.text
            for chunk in self.chunks
        ]

        self.embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        print(
            "[RAG] Ready: "
            f"matrix shape = "
            f"{self.embeddings.shape}"
        )

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[RetrievalResult]:

        if not self.chunks:
            return []

        query_vector = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        scores = (
            self.embeddings
            @ query_vector
        )

        top_k = min(
            top_k,
            len(self.chunks),
        )

        indices = np.argsort(
            scores
        )[::-1][:top_k]

        results = []

        for index in indices:
            chunk = self.chunks[
                int(index)
            ]

            results.append(
                RetrievalResult(
                    source=chunk.source,
                    chunk_id=chunk.chunk_id,
                    score=float(
                        scores[index]
                    ),
                    text=chunk.text,
                )
            )

        return results
