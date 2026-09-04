from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentChunk:
    source: str
    chunk_id: int
    text: str


def chunk_text(text: str) -> list[str]:
    sections = []
    current = []

    for line in text.splitlines():
        if line.startswith("## ") and current:
            chunk = "\n".join(current).strip()

            if chunk:
                sections.append(chunk)

            current = []

        current.append(line)

    if current:
        chunk = "\n".join(current).strip()

        if chunk:
            sections.append(chunk)

    return sections


def load_knowledge_chunks(
    knowledge_dir: str | Path,
) -> list[DocumentChunk]:

    knowledge_dir = Path(knowledge_dir).resolve()

    chunks: list[DocumentChunk] = []

    for file_path in sorted(knowledge_dir.glob("*.md")):

        text = file_path.read_text(
            encoding="utf-8"
        )

        file_chunks = chunk_text(text)

        for index, chunk in enumerate(file_chunks):

            chunks.append(
                DocumentChunk(
                    source=file_path.name,
                    chunk_id=index,
                    text=chunk,
                )
            )

    return chunks
