import redis
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import Binary
from datetime import datetime
import os
from dotenv import load_dotenv
import json

load_dotenv()

class RedisService:
    def __init__(self):
         # Kết nối Redis sử dụng URL từ biến môi trường
        redis_url = os.getenv('REDIS_HOST')
        self.redis_client = redis.from_url(redis_url)
        
        self.mongo_client = AsyncIOMotorClient(os.getenv("MONGODB_URI"), uuidRepresentation='standard')
        self.db = self.mongo_client.data_management
        self.tasks_collection = self.db.tasks
        self.results_collection = self.db.results

    async def update_popular_topics(self):
        """Cập nhật danh sách 5 chủ đề phổ biến từ MongoDB vào Redis"""
        try:
            # Lấy 5 chủ đề được tìm kiếm nhiều nhất trong 24h qua
            pipeline = [
                {
                    "$match": {
                        "created_at": {
                            "$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                        }
                    }
                },
                {"$unwind": "$topics"},
                {"$group": {"_id": "$topics", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            
            cursor = self.tasks_collection.aggregate(pipeline)
            popular_topics = []
            async for doc in cursor:
                popular_topics.append(doc["_id"])
            
            # Lưu vào Redis
            self.redis_client.set("popular_topics", json.dumps(popular_topics))
            print(f"Updated popular topics: {popular_topics}")
        except Exception as e:
            print(f"Error updating popular topics: {str(e)}")

    async def update_topic_data(self):
        """Cập nhật dữ liệu đã crawl cho từng chủ đề phổ biến"""
        try:
            # Lấy danh sách chủ đề phổ biến từ Redis
            popular_topics = json.loads(self.redis_client.get("popular_topics") or "[]")
            
            for topic in popular_topics:
                # Lấy 5 kết quả mới nhất cho mỗi chủ đề
                cursor = self.results_collection.find(
                    {"topic": topic}
                ).sort("created_at", -1).limit(5)
                
                results = []
                async for doc in cursor:
                    results.append({
                        "resultId": str(doc["result_id"]),
                        "source": doc["source"],
                        "text": doc["text"],
                        "created_at": doc["created_at"].isoformat()
                    })
                
                # Lưu vào Redis với key là topic
                self.redis_client.set(f"topic:{topic}", json.dumps(results))
                print(f"Updated data for topic: {topic}")
        except Exception as e:
            print(f"Error updating topic data: {str(e)}")

    async def start_update_loop(self):
        """Bắt đầu vòng lặp cập nhật dữ liệu mỗi 5 phút"""
        while True:
            await self.update_popular_topics()
            await self.update_topic_data()
            await asyncio.sleep(300)  # 5 phút

    def get_popular_topics(self):
        """Lấy danh sách chủ đề phổ biến từ Redis"""
        try:
            topics = self.redis_client.get("popular_topics")
            return json.loads(topics) if topics else []
        except Exception as e:
            print(f"Error getting popular topics: {str(e)}")
            return []

    def get_topic_data(self, topic: str):
        """Lấy dữ liệu đã crawl cho một chủ đề cụ thể"""
        try:
            data = self.redis_client.get(f"topic:{topic}")
            return json.loads(data) if data else []
        except Exception as e:
            print(f"Error getting topic data: {str(e)}")
            return [] 