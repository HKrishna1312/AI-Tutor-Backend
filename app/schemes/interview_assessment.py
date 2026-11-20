from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _required_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("This field cannot be blank")
    return value


class TranscriptTurn(BaseModel):
    speaker: str = Field(max_length=20)
    text: str = Field(max_length=30000)

    @field_validator("speaker")
    @classmethod
    def validate_speaker(cls, value: str) -> str:
        normalized = value.strip().casefold()
        aliases = {
            "assistant": "assistant",
            "agent": "assistant",
            "ai": "assistant",
            "human": "human",
            "user": "human",
            "candidate": "human",
        }
        if normalized not in aliases:
            raise ValueError("speaker must be assistant or human")
        return aliases[normalized]

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _required_text(value)


class ProcessInterviewRequest(BaseModel):
    title: str = Field(default="Interview practice", max_length=255)
    transcript: list[TranscriptTurn] = Field(min_length=2, max_length=200)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _required_text(value)


class AnswerEvaluation(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    feedback: str = Field(min_length=1)


class AttemptResponse(AnswerEvaluation):
    id: int
    session_id: int
    question: str
    concept: str
    answer: str
    created_at: datetime


class ConceptProgress(BaseModel):
    name: str
    average_score: float
    attempts: int


class ProgressResponse(BaseModel):
    session_id: int
    overall_score: float | None
    attempts: int
    weak_concepts: list[ConceptProgress]
    focus_areas: list[str]


class ProcessInterviewResponse(ProgressResponse):
    title: str
    processed_answers: list[AttemptResponse]
