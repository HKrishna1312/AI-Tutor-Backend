
from typing import Any
from pydantic import BaseModel, Field
class IndeedJobSearchRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    location: str = Field(..., min_length=1, max_length=200)
    country: str | None = Field(default=None, max_length=100)
    date_posted: int | None = Field(default=None, ge=1)


class IndeedJobSearchResponse(BaseModel):
    status: str
    query: dict[str, Any]
    count: int
    jobs: list[dict[str, Any]]
