
from google import genai
from google.genai import types
from pinecone import Pinecone

from app.core.config import settings


# -----------------------------------------
# Initialize clients
# -----------------------------------------

gemini_client = genai.Client(
    api_key=settings.GOOGLE_API_KEY
)

pinecone_client = Pinecone(
    api_key=settings.PINECONE_API_KEY
)

index = pinecone_client.Index(
    settings.PINECONE_INDEX_NAME
)


# -----------------------------------------
# Create query embedding
# -----------------------------------------

def create_query_embedding(query: str):

    response = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    return response.embeddings[0].values


# -----------------------------------------
# Retrieve relevant resume chunks
# -----------------------------------------

def retrieve_resume_chunks(
    query: str,
    user_id: str,
    top_k: int = 5
):

    query_embedding = create_query_embedding(query)

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        namespace=settings.PINECONE_NAMESPACE,
        filter={
            "user_id": {
                "$eq": str(user_id)
            }
        }
    )
    print("Pinecone results")
    print(results)
    chunks = []

    for match in results.get("matches", []):

        metadata = match.get("metadata", {})

        text = metadata.get("text")

        if text:

            chunks.append({
                "text": text,
                "score": match.get("score"),
                "file_id": metadata.get("file_id"),
                "filename": metadata.get("filename"),
                "chunk_number": metadata.get("chunk_number")
            })

    return chunks