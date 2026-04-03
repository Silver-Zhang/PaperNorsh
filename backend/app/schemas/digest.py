import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class DigestPaperEntry(BaseModel):
    paper_id: str
    relevance_score: float
    rank: int


class DigestBase(BaseModel):
    date: date
    status: str
    papers: list[DigestPaperEntry] = []


class DigestRead(DigestBase):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    email_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DigestListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    date: date
    status: str
    paper_count: int
    email_sent_at: Optional[datetime] = None
    created_at: datetime
