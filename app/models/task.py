from datetime import datetime, UTC
from typing import List, Optional
from pydantic import BaseModel, Field

class TaskStatus(str):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    job_id: str
    userId: str
    input_user: str
    topics: List[str]
    sources: List[str]  
    audience: str
    style: str
    language: str
    length: str
    status: TaskStatus = TaskStatus.PENDING
    result_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: Optional[str] = None 