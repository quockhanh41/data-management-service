from datetime import datetime, UTC
import logging
from ..models.task import Task, TaskStatus
from ..services.crawler import Crawler
from ..services.gemini_service import GeminiService
from ..services.mongodb_service import MongoDBService
from ..services.rabbitmq_service import RabbitMQService
from ..services.redis_service import RedisService
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CrawlService:
    def __init__(self):
        self.mongodb_service = MongoDBService()
        self.redis_service = RedisService()
        self.rabbitmq_service = RabbitMQService()
        self.gemini_service = GeminiService()
        self.crawler = Crawler(self.redis_service, self.mongodb_service)

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
        crawler = None

        try:
            logger.info(f"Processing task {task_id}")
            # Cập nhật trạng thái task
            await self.mongodb_service.update_task_status(task_id, TaskStatus.IN_PROGRESS)
            
            # Thực hiện crawl dữ liệu cho từng chủ đề
            for topic in crawl_data["topics"]:
                try:
                    logger.info(f"Crawling topic: {topic}")
                    crawler = Crawler(self.redis_service, self.mongodb_service)
                    results = await crawler.crawl(
                        task_id=task_id,
                        topic=topic,
                        sources=crawl_data["sources"],
                        language=crawl_data["language"]
                    )
                    
                    # Kiểm tra kết quả crawl chi tiết
                    if not results:
                        logger.warning(f"No results returned for topic {topic}")
                        continue
                        
                    # Kiểm tra từng nguồn dữ liệu
                    valid_results = {source: content for source, content in results.items() 
                                   if content and content.strip()}
                    
                    if not valid_results:
                        logger.warning(f"No valid content found for topic {topic}")
                        continue
                        
                    logger.info(f"Successfully crawled topic {topic} from sources: {list(valid_results.keys())}")
                except Exception as e:
                    logger.error(f"Error crawling topic {topic}: {str(e)}")
                    continue
                finally:
                    if crawler:
                        await crawler.close()
                        crawler = None
            
            # Cập nhật trạng thái hoàn thành
            await self.mongodb_service.update_task_status(task_id, TaskStatus.COMPLETED)
            logger.info(f"Task {task_id} completed successfully")
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            # Cập nhật trạng thái lỗi
            await self.mongodb_service.update_task_status(task_id, TaskStatus.FAILED, str(e))
        finally:
            if crawler:
                await crawler.close() 