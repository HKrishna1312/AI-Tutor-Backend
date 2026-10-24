from typing import Any
from pydantic import BaseModel, Field


class IndeedJobSearchRequest(BaseModel):
    keyword: str = Field(default="Staff Distributed Systems Architect Python Kafka", max_length=200)
    location: str = Field(default="San Francisco", max_length=200)
    country: str | None = Field(default=None, max_length=100)


class IndeedJobSearchResponse(BaseModel):
    status: str
    query: dict[str, Any]
    count: int
    jobs: list[dict[str, Any]]
