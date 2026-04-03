import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class AuthorSchema(BaseModel):
    name: str
    affiliation: Optional[str] = None


class PaperBase(BaseModel):
    title: str
    authors: list[AuthorSchema] = []
    abstract: Optional[str] = None
    source: str
    source_id: str
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: str
    published_date: Optional[date] = None
    journal_name: Optional[str] = None
    venue: Optional[str] = None
    keywords: list[str] = []


class PaperRead(PaperBase):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    ai_summary: Optional[str] = None
    ai_summary_generated_at: Optional[datetime] = None
    created_at: datetime
    dedup_hash: str


class PaperListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    authors: list[AuthorSchema] = []
    source: str
    published_date: Optional[date] = None
    journal_name: Optional[str] = None
    keywords: list[str] = []
    url: str


class PaperFilter(BaseModel):
    source: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    keyword: Optional[str] = None
    page: int = 1
    per_page: int = 20


class InteractionCreate(BaseModel):
    action: str  # saved / ignored / highly_relevant


class InteractionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    paper_id: uuid.UUID
    action: str
    relevance_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
