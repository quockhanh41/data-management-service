import wikipediaapi
from typing import List, Dict, Optional
import logging
import os
import requests
import asyncio
from datetime import datetime, UTC
import json
from bson.objectid import ObjectId


logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, redis_service, mongodb_service):
        """Khởi tạo Crawler
        
        Args:
            redis_service: Redis service instance
            mongodb_service: MongoDB service instance
        """
        # User agent format: <project-name>/<version> (<contact-url>; <email>)
        # Ví dụ: TKPM-Data-Crawler/1.0 (https://github.com/quockhanh41/User-Management-Service.git; quockhanh41@gmail.com)
        self.wiki = wikipediaapi.Wikipedia(
            user_agent=os.getenv('WIKIPEDIA_API_USER_AGENT'),
            language='en'  # Default language, will be changed in crawl_wikipedia
        )
        self.redis_service = redis_service
        self.mongodb_service = mongodb_service

    async def check_redis_cache(self, topic: str, language: str) -> Optional[tuple]:
        """Kiểm tra dữ liệu trong Redis cache
        
        Args:
            topic: Chủ đề cần kiểm tra
            language: Ngôn ngữ
            
        Returns:
            tuple: (content, result_id) từ cache nếu có, None nếu không có
        """
        try:
            cached_content = await self.redis_service.get_topic_data(topic, language)
            if cached_content:
                logger.info(f"Found cached content for {topic} in {language}")
                # Parse JSON data từ Redis
                data = json.loads(cached_content)
                return data.get("text"), data.get("resultId")
            return None
        except Exception as e:
            logger.error(f"Error checking Redis cache: {str(e)}")
            return None

    async def check_mongodb(self, topic: str, language: str) -> Optional[tuple]:
        """Kiểm tra dữ liệu trong MongoDB
        
        Args:
            topic: Chủ đề cần kiểm tra
            language: Ngôn ngữ
            
        Returns:
            tuple: (text, _id) từ MongoDB nếu có, None nếu không có
        """
        try:
            result = await self.mongodb_service.results_collection.find_one({
                "topic": topic,
                "language": language
            })
            if result:
                logger.info(f"Found content in MongoDB for {topic} in {language}")
                return result["text"], str(result["_id"])
            return None
        except Exception as e:
            logger.error(f"Error checking MongoDB: {str(e)}")
            return None

    async def crawl_wikipedia(self, topic: str, language: str) -> tuple:
        """Crawl dữ liệu từ Wikipedia
        
        Args:
            topic: Chủ đề cần crawl
            language: Ngôn ngữ
            
        Returns:
            tuple: (content, None) nếu crawl thành công, ("", None) nếu thất bại
        """
        try:
            # Sử dụng instance Wikipedia đã được tạo trong __init__
            self.wiki.language = language
            
            # Lấy trang
            page = self.wiki.page(topic)
            
            if page.exists():
                content = page.text
                # Lưu vào Redis set TTL is 1 hour
                await self.redis_service.redis_client.set(f"topic: {topic}, language: {language}", json.dumps(content), ex=3600)
                return content, None
            else:
                logger.warning(f"Wikipedia page not found for topic: {topic}")
                return "", None
        except Exception as e:
            logger.error(f"Error crawling Wikipedia: {str(e)}")
            return "", None

    async def crawl_nature(self, topic: str, language: str) -> str:
        # Implement Nature crawling logic
        try:
            # Implement Nature crawling logic
            api_key = os.getenv('NATURE_API_KEY')
            api_url = os.getenv('NATURE_API_URL')

            # Tạo truy vấn tìm kiếm 
            query = f"q={topic}&api_key={api_key}&p=10"  # Lấy tối đa 10 kết quả

            # Gửi yêu cầu GET đến API
            response = requests.get(f"{api_url}/search", params=query)
            response.raise_for_status()  # Ném ra lỗi nếu trả về không thành công

            # Xử lý dữ liệu trả về
            data = response.json()
            print(data)

            return ""
        except Exception as e:
            logger.error(f"Error crawling Nature: {str(e)}")
            return ""

    async def crawl_pubmed(self, topic: str) -> str:
        # Implement PubMed crawling logic
        return ""

    async def crawl(self, task_id: str, topic: str, sources: List[str], language: str) -> Dict[str, str]:
        """Crawl dữ liệu từ nhiều nguồn
        
        Args:
            task_id: ID của task
            topic: Chủ đề cần crawl
            sources: Danh sách nguồn dữ liệu
            language: Ngôn ngữ
            
        Returns:
            Dict[str, str]: Kết quả crawl từ các nguồn
        """
        results = {}
        for source in sources:
            if source == "wikipedia":
                try:
                    # Tạo các task cho 3 nguồn dữ liệu
                    redis_task = asyncio.create_task(self.check_redis_cache(topic, language))
                    mongodb_task = asyncio.create_task(self.check_mongodb(topic, language))
                    wiki_task = asyncio.create_task(self.crawl_wikipedia(topic, language))
                    
                    # Đợi task đầu tiên hoàn thành và có kết quả khác None
                    while True:
                        done, pending = await asyncio.wait(
                            [redis_task, mongodb_task, wiki_task],
                            return_when=asyncio.FIRST_COMPLETED
                        )
                        
                        completed_task = done.pop()
                        result = completed_task.result()
                        
                        # Nếu có kết quả hợp lệ, dừng vòng lặp
                        if result is not None and result[0] != "":
                            # Hủy các task còn lại
                            for task in pending:
                                task.cancel()
                            break
                            
                        # Nếu wiki_task trả về kết quả rỗng, dừng vòng lặp
                        if completed_task == wiki_task:
                            # Hủy các task còn lại
                            for task in pending:
                                task.cancel()
                            break
                            
                        # Nếu không có kết quả, tiếp tục đợi task khác
                        if completed_task == redis_task:
                            redis_task = asyncio.create_task(self.check_redis_cache(topic, language))
                        elif completed_task == mongodb_task:
                            mongodb_task = asyncio.create_task(self.check_mongodb(topic, language))
                        else:
                            wiki_task = asyncio.create_task(self.crawl_wikipedia(topic, language))
                    
                    content, result_id = result
                    
                    # Xác định nguồn dữ liệu
                    if completed_task == redis_task:
                        logger.info(f"Using cached content from Redis for topic {topic}")
                    elif completed_task == mongodb_task:
                        logger.info(f"Using content from MongoDB for topic {topic}")
                    else:
                        logger.info(f"Using content from Wikipedia for topic {topic}")
                        # Lưu vào MongoDB nếu có dữ liệu mới từ Wikipedia
                        if content:
                            try:
                                result_id = await self.mongodb_service.insert_result(
                                    task_id=task_id,
                                    topic=topic,
                                    source=source,
                                    language=language,
                                    text=content
                                )
                                if result_id:
                                    logger.info(f"Successfully inserted result for topic {topic} with ID {result_id}")
                                else:
                                    logger.error(f"Failed to insert result for topic {topic} - No result ID returned")
                            except Exception as e:
                                logger.error(f"Error inserting result into MongoDB for topic {topic}: {str(e)}")
                    
                    # Thêm result_id vào mảng result_ids của task nếu có
                    if result_id:
                        try:
                            await self.mongodb_service.tasks_collection.update_one(
                                {"_id": ObjectId(task_id)},
                                {
                                    "$addToSet": {"result_ids": result_id},
                                    "$set": {"updated_at": datetime.now(UTC)}
                                }
                            )
                            logger.info(f"Added result_id {result_id} to task {task_id}")
                        except Exception as e:
                            logger.error(f"Error adding result_id to task {task_id}: {str(e)}")
                    
                    results[source] = content
                    
                except Exception as e:
                    logger.error(f"Error processing Wikipedia crawl for topic {topic}: {str(e)}")
                    results[source] = ""
            elif source == "nature":
                results[source] = await self.crawl_nature(topic, language)
            elif source == "pubmed":
                results[source] = await self.crawl_pubmed(topic)
        return results

    async def close(self):
        """Đóng kết nối"""
        # No need to close anything for wikipedia-api
        pass 

# # test wikipedia
# if __name__ == "__main__":
#     import asyncio
    
#     async def main():
#         crawler = Crawler()
#         result = await crawler.crawl_wikipedia("AI", "en")
#         print(result)
#         await crawler.close()
    
#     asyncio.run(main())
