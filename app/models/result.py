from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List

class Result(BaseModel):
    result_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    topic: str
    source: str
    language: str
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow) 