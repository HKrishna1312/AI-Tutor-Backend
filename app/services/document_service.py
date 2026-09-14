import os
import uuid

from fastapi import UploadFile, HTTPException

from pypdf import PdfReader
from docx import Document

from google import genai

from pinecone import Pinecone
from app.core.config import settings
from google.genai import types


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
# PDF text extraction
# -----------------------------------------

def extract_text_from_pdf(file_path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# -----------------------------------------
# DOCX text extraction
# -----------------------------------------

def extract_text_from_docx(file_path):

    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:

        if paragraph.text.strip():

            text += paragraph.text + "\n"

    return text


# -----------------------------------------
# Text chunking
# -----------------------------------------

def split_text(text, chunk_size=1000):

    words = text.split()

    chunks = []

    current_chunk = []
    current_length = 0

    for word in words:

        current_chunk.append(word)

        current_length += len(word)

        if current_length >= chunk_size:

            chunks.append(
                " ".join(current_chunk)
            )

            current_chunk = []
            current_length = 0

    if current_chunk:

        chunks.append(
            " ".join(current_chunk)
        )

    return chunks


# -----------------------------------------
# Gemini embeddings
# -----------------------------------------
def create_embeddings(chunks):

    embeddings = []

    for chunk in chunks:

        response = gemini_client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunk,
            config=types.EmbedContentConfig(
                output_dimensionality=768
            )
        )

        embeddings.append(
            response.embeddings[0].values
        )

    return embeddings


# -----------------------------------------
# Process document
# -----------------------------------------

async def process_document(file: UploadFile):

    filename = file.filename

    if not filename:

        raise HTTPException(
            status_code=400,
            detail="File name is missing"
        )

    extension = os.path.splitext(
        filename
    )[1].lower()

    # Check file type

    if extension not in [".pdf", ".docx"]:

        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )

    # -----------------------------------------
    # Create temporary file
    # -----------------------------------------

    file_id = str(uuid.uuid4())

    os.makedirs(
        "temp",
        exist_ok=True
    )

    file_path = os.path.join(
        "temp",
        f"{file_id}{extension}"
    )

    # -----------------------------------------
    # Save uploaded file
    # -----------------------------------------

    content = await file.read()

    with open(file_path, "wb") as buffer:

        buffer.write(content)

    # -----------------------------------------
    # Extract text
    # -----------------------------------------

    if extension == ".pdf":

        text = extract_text_from_pdf(
            file_path
        )

    else:

        text = extract_text_from_docx(
            file_path
        )

    # -----------------------------------------
    # Check text
    # -----------------------------------------

    if not text.strip():

        os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail="Could not extract text from document"
        )

    # -----------------------------------------
    # Split text
    # -----------------------------------------

    chunks = split_text(
        text
    )

    # -----------------------------------------
    # Create Gemini embeddings
    # -----------------------------------------

    embeddings = create_embeddings(
        chunks
    )

    # -----------------------------------------
    # Prepare Pinecone vectors
    # -----------------------------------------

    vectors = []

    for i, embedding in enumerate(embeddings):

        vector_id = (
            f"{file_id}-chunk-{i}"
        )

        vectors.append(
            {
                "id": vector_id,

                "values": embedding,

                "metadata": {
                    "file_id": file_id,
                    "filename": filename,
                    "chunk_number": i,
                    "text": chunks[i]
                }
            }
        )

    # -----------------------------------------
    # Store in Pinecone
    # -----------------------------------------

    index.upsert(
        vectors=vectors,
        namespace=settings.PINECONE_NAMESPACE
    )

    # -----------------------------------------
    # Remove temporary file
    # -----------------------------------------

    os.remove(file_path)

    return {
        "message": "Document processed successfully",

        "file_id": file_id,

        "filename": filename,

        "chunks": len(chunks),

        "embedding_model": "gemini-embedding-001",

        "vector_database": "Pinecone"
    }