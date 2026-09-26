import json
import os

from dotenv import load_dotenv
import faiss
from google import genai

from document_loader import load_and_chunk_documents

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMBEDDING_MODEL = "gemini-embedding-001"

INDEX_PATH = "documents.index"
CHUNKS_PATH = "chunks.json"


def create_embedding(text: str):
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    return response.embeddings[0].values


def build_index():
    chunks = load_and_chunk_documents()

    if not chunks:
        raise ValueError("No documents found.")

    embeddings = [
        create_embedding(chunk["content"])
        for chunk in chunks
    ]

    dimension = len(embeddings[0])

    index = faiss.IndexFlatL2(dimension)

    import numpy as np

    vectors = np.array(
        embeddings,
        dtype="float32"
    )

    index.add(vectors)

    faiss.write_index(index, INDEX_PATH)

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    print(f"Indexed {len(chunks)} chunks.")
    print(f"Embedding dimension: {dimension}")


if __name__ == "__main__":
    build_index()