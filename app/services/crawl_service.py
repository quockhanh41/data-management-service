from datetime import datetime, UTC
import logging
from ..models.task import Task, TaskStatus
from ..services.crawler import Crawler
from ..services.gemini_service import GeminiService
from ..services.mongodb_service import MongoDBService
from ..services.rabbitmq_service import RabbitMQService
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CrawlService:
    def __init__(self):
        self.mongodb_service = MongoDBService()
        self.rabbitmq_service = RabbitMQService()
        self.gemini_service = GeminiService()

    async def create_crawl_task(self, topic: str, sources: List[str], language: str) -> Dict[str, Any]:
        """Tạo task crawl mới
        
        Args:
            topic: Chủ đề cần crawl
            sources: Danh sách nguồn dữ liệu
            language: Ngôn ngữ
            
        Returns:
            Dict chứa thông tin task và chủ đề đã trích xuất
        """
        try:
            # Trích xuất chủ đề con bằng Gemini
            extracted_topics = await self.gemini_service.extract_topic(topic, language)
            
            # Tạo task mới
            task = Task(
                input_user=topic,
                topics=extracted_topics,
                sources=sources,
                language=language,
                status=TaskStatus.PENDING,
                created_at=datetime.now(UTC)
            )
            
            # Lưu task vào database
            task_dict = task.dict()
            result = await self.mongodb_service.tasks_collection.insert_one(task_dict)
            task_id = str(result.inserted_id)
            
            # Gửi task vào RabbitMQ queue
            await self.rabbitmq_service.publish_crawl_task(
                task_id,
                {
                    "topics": extracted_topics,
                    "sources": sources,
                    "language": language
                }
            )
            
            logger.info(f"Created new crawl task {task_id}")
            return {
                "message": "Đang tiến hành crawl dữ liệu...",
                "taskId": task_id,
                "extractedTopics": extracted_topics
            }
        except Exception as e:
            logger.error(f"Error creating crawl task: {str(e)}")
            raise

    async def process_crawl_task(self, data: Dict[str, Any]):
        """Xử lý task crawl từ RabbitMQ
        
        Args:
            data: Dữ liệu task từ RabbitMQ
        """
        task_id = data["task_id"]
        crawl_data = data["data"]
        
        crawler = Crawler()
        try:
            logger.info(f"Processing task {task_id}")
            # Cập nhật trạng thái task
            await self.mongodb_service.update_task_status(task_id, TaskStatus.IN_PROGRESS)
            
            # Thực hiện crawl dữ liệu
            for topic in crawl_data["topics"]:
                logger.info(f"Crawling topic: {topic}")
                results = await crawler.crawl(topic, crawl_data["sources"], crawl_data["language"])
                
                for source, text in results.items():
                    if text:
                        logger.info(f"Found content from {source}")
                        # Thêm kết quả vào database
                        await self.mongodb_service.insert_result(
                            task_id=task_id,
                            topic=topic,
                            source=source,
                            language=crawl_data["language"],
                            text=text
                        )
            
            # Cập nhật trạng thái hoàn thành
            await self.mongodb_service.update_task_status(task_id, TaskStatus.COMPLETED)
            logger.info(f"Task {task_id} completed successfully")
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            # Cập nhật trạng thái lỗi
            await self.mongodb_service.update_task_status(task_id, TaskStatus.FAILED, str(e))
        finally:
            await crawler.close() 