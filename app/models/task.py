from datetime import datetime, UTC
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    userId: str
    input_user: str
    topics: List[str]
    sources: List[str]  
    audience: str
    style: str
    language: str
    length: str
    limit: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: Optional[str] = None 