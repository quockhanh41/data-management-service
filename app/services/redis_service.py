import redis.asyncio as redis
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import Binary
from datetime import datetime, UTC
import os
from dotenv import load_dotenv
import json
import logging
from app.services.mongodb_service import MongoDBService

load_dotenv()

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        """Khởi tạo Redis client"""
        self.redis_client = None
        self._update_task = None
        self._is_running = False
        self._max_retries = 3
        self._retry_delay = 5  # giây

        self.mongo_client = AsyncIOMotorClient(os.getenv("MONGODB_URI"), uuidRepresentation='standard')
        self.db = self.mongo_client.data_management
        self.tasks_collection = self.db.tasks
        self.results_collection = self.db.results

    async def connect(self):
        """Kết nối đến Redis server với retry"""
        retry_count = 0
        while retry_count < self._max_retries:
            try:
                # Lấy thông tin kết nối từ biến môi trường
                redis_url = os.getenv("REDIS_URL")
                if not redis_url:
                    raise ValueError("REDIS_URL environment variable is not set")

                # Tạo kết nối Redis
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )

                # Kiểm tra kết nối
                await self.redis_client.ping()
                logger.info("Successfully connected to Redis")
                return

            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to connect to Redis (attempt {retry_count}/{self._max_retries}): {str(e)}")
                
                if retry_count < self._max_retries:
                    logger.info(f"Retrying in {self._retry_delay} seconds...")
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error("Max retries reached. Could not connect to Redis")
                    raise

    async def close(self):
        """Đóng kết nối Redis và dừng task cập nhật"""
        if self._update_task:
            self._is_running = False
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    async def _ensure_connection(self):
        """Đảm bảo kết nối Redis đang hoạt động"""
        if not self.redis_client:
            await self.connect()
        try:
            await self.redis_client.ping()
        except Exception:
            logger.warning("Redis connection lost, attempting to reconnect...")
            await self.connect()

    async def update_popular_topics_for_redis(self, topics: list):
        """Cập nhật danh sách chủ đề phổ biến vào Redis"""
        try:
            await self._ensure_connection()
            await self.redis_client.set(
                "popular_topics",
                json.dumps(topics)
            )
            logger.info(f"Updated list of {len(topics)} popular topics in Redis")
        except Exception as e:
            logger.error(f"Error updating popular topics: {str(e)}")
            raise

    async def get_popular_topics_from_redis(self) -> list:
        """Lấy danh sách chủ đề phổ biến từ Redis"""
        try:
            await self._ensure_connection()
            topics_json = await self.redis_client.get("popular_topics")
            if topics_json:
                return json.loads(topics_json)
            return []
        except Exception as e:
            logger.error(f"Error getting popular topics: {str(e)}")
            return []

    async def update_popular_topics_from_mongodb_to_redis(self):
        """Cập nhật danh sách chủ đề phổ biến từ MongoDB"""
        try:
            mongodb_service = MongoDBService()
            popular_topics = await mongodb_service.get_popular_topics()
            print(popular_topics)
            await self.update_popular_topics_for_redis(popular_topics)
            logger.info(f"Updated Redis with {len(popular_topics)} topics from MongoDB")
        except Exception as e:
            logger.error(f"Error updating from MongoDB: {str(e)}")

    async def start_update_loop(self):
        """Bắt đầu vòng lặp cập nhật Redis tự động"""
        if self._is_running:
            return

        self._is_running = True
        self._update_task = asyncio.create_task(self._update_loop())

    async def _update_loop(self):
        """Vòng lặp cập nhật Redis mỗi 30 phút"""
        while self._is_running:
            try:
                await self.update_popular_topics_from_mongodb_to_redis()
                await self.update_topic_data()
                logger.info(f"Redis update completed at {datetime.now(UTC)}")
            except Exception as e:
                logger.error(f"Error in update loop: {str(e)}")
            
            # Đợi 30 phút trước khi cập nhật lại
            await asyncio.sleep(1800)  # 1800 giây = 30 phút

    async def update_topic_data(self):
        """Cập nhật dữ liệu đã crawl cho từng chủ đề phổ biến"""
        try:
            # Lấy danh sách chủ đề phổ biến từ Redis
            popular_topics = await self.get_popular_topics_from_redis()
            print(popular_topics)
            
            for topic in popular_topics:
                try:
                    # Lấy 1 kết quả mới nhất cho mỗi chủ đề từ mongodb dựa vào bảng results
                    cursor = self.results_collection.find(
                        {"topic": topic}
                    ).sort("created_at", -1).limit(1)
                    
                    results = []
                    async for doc in cursor:
                        results.append({
                            "resultId": str(doc["_id"]),
                            "source": doc["source"],
                            "language": doc["language"],
                            "text": doc["text"],
                            "created_at": doc["created_at"].isoformat()
                        })
                    
                    if results:
                        # Lưu vào Redis với key là topic và language
        
                        await self.redis_client.set(
                            f"topic: {topic}, language: {results[0]['language']}", 
                            json.dumps(results[0])
                        )
                        logger.info(f"Updated data for topic: {topic} in language: {results[0]['language']}")
                    else:
                        logger.warning(f"No results found for topic: {topic}")
                        
                except Exception as e:
                    logger.error(f"Error processing topic {topic}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error updating topic data: {str(e)}")

    async def get_topic_data(self, topic: str, language: str):
        """Lấy dữ liệu đã crawl cho một chủ đề cụ thể"""
        try:
            await self._ensure_connection()
            data = await self.redis_client.get(f"topic: {topic}, language: {language}")
            if data:
                return json.loads(data)
            return []
        except Exception as e:
            logger.error(f"Error getting topic data: {str(e)}")
            return [] 