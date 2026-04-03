import uuid
from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel


class PreferenceBase(BaseModel):
    keywords: list[str] = []
    exclude_keywords: list[str] = []
    preferred_topics: list[str] = []
    follow_authors: list[str] = []
    preferred_sources: list[str] = ["arxiv", "openalex", "crossref"]
    preferred_journals: list[str] = []
    delivery_time: time = time(8, 0, 0)
    max_papers_per_digest: int = 20


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceUpdate(BaseModel):
    keywords: Optional[list[str]] = None
    exclude_keywords: Optional[list[str]] = None
    preferred_topics: Optional[list[str]] = None
    follow_authors: Optional[list[str]] = None
    preferred_sources: Optional[list[str]] = None
    preferred_journals: Optional[list[str]] = None
    delivery_time: Optional[time] = None
    max_papers_per_digest: Optional[int] = None


class PreferenceRead(PreferenceBase):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
