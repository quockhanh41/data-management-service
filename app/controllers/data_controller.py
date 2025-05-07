from fastapi import APIRouter, HTTPException
from typing import List
from ..models.task import Task, TaskStatus
from ..models.result import Result
from ..services.redis_service import RedisService
from ..services.mongodb_service import MongoDBService
from ..services.crawl_service import CrawlService
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Khởi tạo router
router = APIRouter()

# Khởi tạo các services
redis_service = RedisService()
mongodb_service = MongoDBService()
crawl_service = CrawlService()

class CrawlRequest(BaseModel):
    userId: str
    topic: str
    sources: List[str]
    audience: str
    style: str
    language: str
    length: str
    limit: int = 1

class CrawlResponse(BaseModel):
    message: str
    job_id: str
    extractedTopics: List[str]

class CrawlStatusResponse(BaseModel):
    taskId: str
    status: str
    resultIds: List[str]

class ResultResponse(BaseModel):
    resultId: str
    topic: str
    source: str
    language: str
    text: str

@router.get("/data/suggestions")
async def get_popular_topics():
    """Lấy danh sách chủ đề phổ biến"""
    return await redis_service.get_popular_topics_from_redis()

@router.post("/data/crawl", response_model=CrawlResponse)
async def crawl_data(request: CrawlRequest):
    """Tạo task crawl mới"""
    return await crawl_service.create_crawl_task(
        userId=request.userId,
        topic=request.topic,
        sources=request.sources,
        audience=request.audience,
        style=request.style,
        language=request.language,
        length=request.length,
        limit=request.limit
    )

@router.get("/data/status/{task_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(task_id: str):
    """Lấy trạng thái của task"""
    task = await mongodb_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return CrawlStatusResponse(
        taskId=task_id,
        status=task["status"],
        resultIds=task.get("result_ids", [])
    )

@router.get("/data/result/{result_id}", response_model=ResultResponse)
async def get_result(result_id: str):
    """Lấy kết quả crawl theo ID"""
    result = await mongodb_service.get_result(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return ResultResponse(
        resultId=result_id,
        topic=result["topic"],
        source=result["source"],
        language=result["language"],
        text=result["text"]
    ) 