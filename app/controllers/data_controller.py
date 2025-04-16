from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from ..models.task import Task, TaskStatus
from ..models.result import Result
from ..services.crawler import Crawler
from ..services.gemini_service import GeminiService
from ..services.redis_service import RedisService
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from bson import Binary

load_dotenv()

router = APIRouter()
client = AsyncIOMotorClient(os.getenv("MONGODB_URI"), uuidRepresentation='standard')
db = client.data_management
tasks_collection = db.tasks
results_collection = db.results

redis_service = RedisService()

# Danh sách các chủ đề phổ biến
POPULAR_TOPICS = [
    "Quantum Mechanics",
    "Black Hole",
    "Artificial Intelligence",
    "Photosynthesis",
    "DNA Replication"
]

class CrawlRequest(BaseModel):
    topic: str
    sources: List[str]
    language: str

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

@router.get("/data/suggestions", response_model=List[str])
async def get_popular_topics():
    return redis_service.get_popular_topics()

@router.post("/data/crawl")
async def crawl_data(request: CrawlRequest):
    # Sử dụng Gemini để trích xuất chủ đề
    gemini_service = GeminiService()
    extracted_topics = await gemini_service.extract_topic(request.topic, request.language)

    
    task = Task(topics=extracted_topics, sources=request.sources, language=request.language)
    task_dict = task.dict()
    task_dict['task_id'] = Binary.from_uuid(task.task_id)
    await tasks_collection.insert_one(task_dict)
    
    crawler = Crawler()
    try:
        task.status = TaskStatus.IN_PROGRESS
        await tasks_collection.update_one(
            {"task_id": Binary.from_uuid(task.task_id)},
            {"$set": {"status": task.status, "updated_at": datetime.utcnow()}}
        )
        
        for topic in extracted_topics:
            results = await crawler.crawl(topic, request.sources, request.language)
            
            for source, text in results.items():
                if text:
                    result = Result(
                        task_id=task.task_id,
                        topic=topic,
                        source=source,
                        language=request.language,
                        text=text
                    )
                    result_dict = result.dict()
                    result_dict['result_id'] = Binary.from_uuid(result.result_id)
                    result_dict['task_id'] = Binary.from_uuid(result.task_id)
                    await results_collection.insert_one(result_dict)
                    task.result_ids.append(result.result_id)
        
        task.status = TaskStatus.COMPLETED
        await tasks_collection.update_one(
            {"task_id": Binary.from_uuid(task.task_id)},
            {"$set": {
                "status": task.status,
                "result_ids": [Binary.from_uuid(id) for id in task.result_ids],
                "updated_at": datetime.utcnow()
            }}
        )
        
        return {
            "message": "Đang tiến hành crawl dữ liệu...",
            "taskId": str(task.task_id),
            "extractedTopics": extracted_topics
        }
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        await tasks_collection.update_one(
            {"task_id": Binary.from_uuid(task.task_id)},
            {"$set": {
                "status": task.status,
                "error": task.error,
                "updated_at": datetime.utcnow()
            }}
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await crawler.close()

@router.get("/data/status/{task_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(task_id: UUID):
    task = await tasks_collection.find_one({"task_id": Binary.from_uuid(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return CrawlStatusResponse(
        taskId=str(task_id),
        status=task["status"],
        resultIds=[str(result_id) for result_id in task.get("result_ids", [])]
    )

@router.get("/data/result/{result_id}", response_model=ResultResponse)
async def get_result(result_id: UUID):
    result = await results_collection.find_one({"result_id": Binary.from_uuid(result_id)})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return ResultResponse(
        resultId=str(result_id),
        topic=result["topic"],
        source=result["source"],
        language=result["language"],
        text=result["text"]
    )

@router.get("/data/tasks/{task_id}")
async def get_task_status(task_id: UUID):
    task = await tasks_collection.find_one({"task_id": Binary.from_uuid(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task 