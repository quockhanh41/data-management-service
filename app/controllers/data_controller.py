from fastapi import APIRouter, HTTPException
from typing import List
from ..models.task import Task, TaskStatus
from ..models.result import Result
from ..services.crawler import Crawler
from ..services.gemini_service import GeminiService
from ..services.redis_service import RedisService
from ..services.rabbitmq_service import RabbitMQService
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, UTC
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import logging
from bson import ObjectId

load_dotenv()

logger = logging.getLogger(__name__)

# Khởi tạo router
router = APIRouter()

# Khởi tạo các services
redis_service = RedisService()
rabbitmq_service = RabbitMQService()
client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client.data_management
tasks_collection = db.tasks
results_collection = db.results

class CrawlRequest(BaseModel):
    topic: str
    sources: List
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

async def process_crawl_task(data: dict):
    """Xử lý task crawl từ RabbitMQ"""
    task_id = data["task_id"]
    crawl_data = data["data"]
    
    crawler = Crawler()
    try:
        logger.info(f"Processing task {task_id}")
        # Cập nhật trạng thái task
        await tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": TaskStatus.IN_PROGRESS, "updated_at": datetime.now(UTC)}}
        )
        
        # Thực hiện crawl dữ liệu
        for topic in crawl_data["topics"]:
            logger.info(f"Crawling topic: {topic}")
            results = await crawler.crawl(topic, crawl_data["sources"], crawl_data["language"])
            
            for source, text in results.items():
                if text:
                    logger.info(f"Found content from {source}")
                    result = {
                        "task_id": ObjectId(task_id),
                        "topic": topic,
                        "source": source,
                        "language": crawl_data["language"],
                        "text": text
                    }
                    result_insert = await results_collection.insert_one(result)
                    
                    # Cập nhật result_ids trong task
                    await tasks_collection.update_one(
                        {"_id": ObjectId(task_id)},
                        {"$push": {"result_ids": str(result_insert.inserted_id)}}
                    )
        
        # Cập nhật trạng thái hoàn thành
        await tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {
                "status": TaskStatus.COMPLETED,
                "updated_at": datetime.now(UTC)
            }}
        )
        logger.info(f"Task {task_id} completed successfully")
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}")
        # Cập nhật trạng thái lỗi
        await tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {
                "status": TaskStatus.FAILED,
                "error": str(e),
                "updated_at": datetime.now(UTC)
            }}
        )
    finally:
        await crawler.close()

@router.get("/data/popular-topics")
async def get_popular_topics():
    return redis_service.get_popular_topics()

@router.post("/data/crawl")
async def crawl_data(request: CrawlRequest):
    # Sử dụng Gemini để trích xuất chủ đề
    gemini_service = GeminiService()
    extracted_topics = await gemini_service.extract_topic(request.topic, request.language)

    # Tạo task mới
    task = Task(topics=extracted_topics, sources=request.sources, language=request.language)
    task_dict = task.dict()
    result = await tasks_collection.insert_one(task_dict)
    task_id = str(result.inserted_id)
    
    # Gửi task vào RabbitMQ queue
    await rabbitmq_service.publish_crawl_task(
        task_id,
        {
            "topics": extracted_topics,
            "sources": request.sources,
            "language": request.language
        }
    )
    
    return {
        "message": "Đang tiến hành crawl dữ liệu...",
        "taskId": task_id,
        "extractedTopics": extracted_topics
    }

@router.get("/data/status/{task_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(task_id: str):
    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return CrawlStatusResponse(
        taskId=task_id,
        status=task["status"],
        resultIds=task.get("result_ids", [])
    )

@router.get("/data/result/{result_id}", response_model=ResultResponse)
async def get_result(result_id: str):
    result = await results_collection.find_one({"_id": ObjectId(result_id)})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return ResultResponse(
        resultId=result_id,
        topic=result["topic"],
        source=result["source"],
        language=result["language"],
        text=result["text"]
    ) 