
from app.services.retrieval_service import retrieve_resume_chunks
from app.services.prompt_service import build_resume_prompt
from app.core.llm_manager import LLMManager


llm_manager = LLMManager()


def generate_resume_answer(
    question: str,
    user_id: str
):

    # 1. Retrieve relevant resume chunks
    retrieved_chunks = retrieve_resume_chunks(
        query=question,
        user_id=user_id,
        top_k=5
    )

    # 2. Build grounded prompt
    prompt = build_resume_prompt(
        question=question,
        retrieved_chunks=retrieved_chunks
    )

    # 3. Generate answer using Gemini
    response = llm_manager.invoke(prompt)

    return {
        "answer": response.content,
        "sources": retrieved_chunks
    }