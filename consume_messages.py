import asyncio
import os
from dotenv import load_dotenv
from app.services.rabbitmq_service import RabbitMQService
from app.services.crawler import Crawler
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, UTC
from app.models.task import TaskStatus
import logging
from bson import ObjectId

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Khởi tạo MongoDB client
client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client.data_management
tasks_collection = db.tasks
results_collection = db.results

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

async def consume_messages():
    """Consume messages từ RabbitMQ"""
    rabbitmq_service = RabbitMQService()
    try:
        # Kết nối đến RabbitMQ
        await rabbitmq_service.connect()
        logger.info("Connected to RabbitMQ")
        
        # Bắt đầu tiêu thụ messages
        await rabbitmq_service.consume_crawl_tasks(process_crawl_task)
        
    except Exception as e:
        logger.error(f"Error consuming messages: {str(e)}")
    finally:
        await rabbitmq_service.close()
        logger.info("Disconnected from RabbitMQ")

if __name__ == "__main__":
    try:
        asyncio.run(consume_messages())
    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}") 