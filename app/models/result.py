from datetime import datetime, UTC
from pydantic import BaseModel, Field

class Result(BaseModel):
    task_id: str
    topic: str
    source: str
    language: str
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC)) 