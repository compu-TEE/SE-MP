from pathlib import Path


DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"


def load_documents():
    documents = []

    for file_path in DOCUMENTS_DIR.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in [".txt", ".md"]:
            text = file_path.read_text(encoding="utf-8")

            documents.append({
                "source": str(file_path.relative_to(DOCUMENTS_DIR)),
                "content": text,
            })

    return documents


def chunk_text(text: str, chunk_size: int = 500):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


def load_and_chunk_documents():
    documents = load_documents()

    chunks = []

    for document in documents:
        document_chunks = chunk_text(document["content"])

        for index, chunk in enumerate(document_chunks):
            chunks.append({
                "source": document["source"],
                "chunk_id": index,
                "content": chunk,
            })

    return chunks