
def build_resume_prompt(
    question: str,
    retrieved_chunks: list
) -> str:

    if not retrieved_chunks:
        context = "No relevant resume information was found."
    else:
        context = "\n\n".join(
            [
                f"Resume context {i + 1}:\n{chunk['text']}"
                for i, chunk in enumerate(retrieved_chunks)
            ]
        )

    prompt = f"""
You are an AI resume assistant.

Your task is to answer the user's question using the provided resume context.

IMPORTANT RULES:
1. Use only information supported by the provided resume context.
2. Do not invent qualifications, experience, skills, or personal details.
3. If the answer cannot be found in the context, clearly say that
   the information is not available in the uploaded resume.
4. Answer clearly and professionally.
5. Do not mention internal retrieval systems, embeddings, or Pinecone.
6. If the user asks for advice, clearly distinguish advice from facts
   found in the resume.

RESUME CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    return prompt