import json
import os

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai

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


def retrieve_documents(query: str, top_k: int = 3):
    index = faiss.read_index(INDEX_PATH)

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    query_embedding = create_embedding(query)

    query_vector = np.array(
        [query_embedding],
        dtype="float32"
    )

    distances, indices = index.search(
        query_vector,
        min(top_k, len(chunks))
    )

    results = []

    for distance, index_position in zip(
        distances[0],
        indices[0]
    ):
        results.append({
            "source": chunks[index_position]["source"],
            "chunk_id": chunks[index_position]["chunk_id"],
            "content": chunks[index_position]["content"],
            "distance": float(distance),
        })

    return results

def rag_answer(query: str):
    results = retrieve_documents(query)

    context = "\n\n".join(
        f"""
SOURCE: {result["source"]}
CHUNK: {result["chunk_id"]}
CONTENT:
{result["content"]}
"""
        for result in results
    )

    prompt = f"""
You are a financial software requirements analysis assistant.

Answer the user's question using ONLY the provided knowledge-base
context.

Do not invent regulations, policies, or requirements.

If the context does not contain enough information to answer the
question, explicitly say that the available evidence is insufficient.

KNOWLEDGE BASE:

{context}

USER QUESTION:

{query}

Return a clear answer.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=prompt,
    )

    return {
        "answer": response.text,
        "sources": [
            {
                "source": result["source"],
                "chunk_id": result["chunk_id"],
                "distance": result["distance"],
            }
            for result in results
        ],
    }

if __name__ == "__main__":
    answer = rag_answer(
        "What security controls are required for money transfers?"
    )

    print(answer)