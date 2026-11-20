import asyncio
import json
import re
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_manager import LLMManager
from app.models.interview_assessment import InterviewAttemptTable, InterviewSessionTable
from app.schemes.interview_assessment import (
    AnswerEvaluation,
    AttemptResponse,
    ConceptProgress,
    ProcessInterviewResponse,
    ProgressResponse,
    TranscriptTurn,
)


llm_manager = LLMManager()


def _normalise_concept(concept: str) -> str:
    return " ".join(concept.strip().split()).casefold()


def _json_object(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Model did not return a JSON object")
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("Model result must be a JSON object")
    return payload


def _as_text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _fallback_evaluation() -> AnswerEvaluation:
    return AnswerEvaluation(
        score=0,
        strengths=[],
        improvements=["Give a direct answer, explain your reasoning, and include a concrete example."],
        feedback="Your answer was saved, but it could not be assessed automatically. Please retry with a detailed response.",
    )


async def evaluate_answer(question: str, concept: str, answer: str) -> AnswerEvaluation:
    prompt = f"""
You are evaluating an interview answer. Return only a JSON object with exactly these keys:
score (integer from 0 to 100), strengths (array of short strings), improvements (array of short strings), feedback (a concise helpful paragraph).

Score correctness, relevance, clarity, and evidence. Do not invent facts that the candidate did not say.

Question: {question}
Concept being tested: {concept}
Candidate answer: {answer}
"""
    try:
        raw = await asyncio.to_thread(llm_manager.invoke_assessment, prompt)
        data = _json_object(raw)
        return AnswerEvaluation(
            score=max(0, min(100, int(data["score"]))),
            strengths=_as_text_list(data.get("strengths")),
            improvements=_as_text_list(data.get("improvements")),
            feedback=str(data["feedback"]).strip(),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return _fallback_evaluation()
    except Exception:
        return _fallback_evaluation()


async def identify_concept(question: str) -> str:
    prompt = f"""
Identify the main interview concept tested by this question. Return only a short lower-case label of at most 120 characters, such as 'python concurrency', 'sql indexing', or 'communication'.

Question: {question}
"""
    try:
        concept = (await asyncio.to_thread(llm_manager.invoke_assessment, prompt)).strip()
        concept = " ".join(concept.replace('"', '').split())
        if not concept or len(concept) > 120:
            raise ValueError("Invalid concept")
        return concept.casefold()
    except Exception:
        return "general interview skills"


async def get_owned_session(db: AsyncSession, session_id: int, user_id: str) -> InterviewSessionTable | None:
    result = await db.execute(
        select(InterviewSessionTable).where(
            InterviewSessionTable.id == session_id,
            InterviewSessionTable.user_id == str(user_id),
        )
    )
    return result.scalar_one_or_none()


async def create_session(db: AsyncSession, user_id: str, title: str) -> InterviewSessionTable:
    session = InterviewSessionTable(user_id=str(user_id), title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def submit_answer(
    db: AsyncSession, session: InterviewSessionTable, question: str, concept: str, answer: str
) -> AttemptResponse:
    evaluation = await evaluate_answer(question, concept, answer)
    attempt = InterviewAttemptTable(
        session_id=session.id,
        question=question,
        concept=_normalise_concept(concept),
        answer=answer,
        score=evaluation.score,
        strengths=json.dumps(evaluation.strengths),
        improvements=json.dumps(evaluation.improvements),
        feedback=evaluation.feedback,
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return AttemptResponse(
        id=attempt.id,
        session_id=attempt.session_id,
        question=attempt.question,
        concept=attempt.concept,
        answer=attempt.answer,
        score=attempt.score,
        strengths=evaluation.strengths,
        improvements=evaluation.improvements,
        feedback=attempt.feedback,
        created_at=attempt.created_at,
    )


def _question_answer_pairs(transcript: list[TranscriptTurn]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    question: str | None = None
    answer_parts: list[str] = []

    for turn in transcript:
        if turn.speaker == "assistant":
            if question and answer_parts:
                pairs.append((question, " ".join(answer_parts)))
            question = turn.text if "?" in turn.text else None
            answer_parts = []
        elif question:
            answer_parts.append(turn.text)

    if question and answer_parts:
        pairs.append((question, " ".join(answer_parts)))
    return pairs


async def process_completed_interview(
    db: AsyncSession,
    user_id: str,
    title: str,
    transcript: list[TranscriptTurn],
) -> ProcessInterviewResponse:
    pairs = _question_answer_pairs(transcript)
    if not pairs:
        raise ValueError("Transcript must include an assistant question followed by a human answer")

    session = await create_session(db, user_id, title)
    processed_answers = []
    for question, answer in pairs:
        concept = await identify_concept(question)
        processed_answers.append(await submit_answer(db, session, question, concept, answer))

    progress = await get_progress(db, session.id)
    return ProcessInterviewResponse(
        **progress.model_dump(),
        title=session.title,
        processed_answers=processed_answers,
    )


async def _attempts(db: AsyncSession, session_id: int) -> list[InterviewAttemptTable]:
    result = await db.execute(
        select(InterviewAttemptTable)
        .where(InterviewAttemptTable.session_id == session_id)
        .order_by(InterviewAttemptTable.created_at, InterviewAttemptTable.id)
    )
    return list(result.scalars())


async def get_progress(db: AsyncSession, session_id: int) -> ProgressResponse:
    attempts = await _attempts(db, session_id)
    grouped: dict[str, list[InterviewAttemptTable]] = defaultdict(list)
    for attempt in attempts:
        grouped[_normalise_concept(attempt.concept)].append(attempt)

    concepts = [
        ConceptProgress(
            name=concept,
            average_score=round(sum(item.score for item in rows) / len(rows), 2),
            attempts=len(rows),
        )
        for concept, rows in grouped.items()
    ]
    concepts.sort(key=lambda item: (item.average_score, item.name))

    focus_areas = []
    for concept in concepts[:3]:
        lowest_attempt = min(grouped[concept.name], key=lambda item: item.score)
        try:
            suggestions = json.loads(lowest_attempt.improvements)
        except (TypeError, ValueError):
            suggestions = []
        if suggestions:
            focus_areas.append(f"{concept.name}: {suggestions[0]}")
        else:
            focus_areas.append(f"{concept.name}: practise explaining this concept with a concrete example.")

    overall = round(sum(item.score for item in attempts) / len(attempts), 2) if attempts else None
    return ProgressResponse(
        session_id=session_id,
        overall_score=overall,
        attempts=len(attempts),
        weak_concepts=concepts,
        focus_areas=focus_areas,
    )


