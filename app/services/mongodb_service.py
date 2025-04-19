from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, UTC
import os
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

class MongoDBService:
    def __init__(self):
        """Khởi tạo kết nối MongoDB"""
        self.client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        self.db = self.client.data_management
        self.tasks_collection = self.db.tasks
        self.results_collection = self.db.results

    async def connect(self):
        """Kiểm tra kết nối MongoDB"""
        try:
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise

    async def close(self):
        """Đóng kết nối MongoDB"""
        self.client.close()
        logger.info("Disconnected from MongoDB")

    async def get_popular_topics(self, limit: int = 5) -> list:
        """Lấy danh sách chủ đề phổ biến từ MongoDB
        
        Args:
            limit: Số lượng chủ đề phổ biến cần lấy (mặc định là 5)
            
        Returns:
            list: Danh sách các chủ đề phổ biến
        """
        try:
            # Lấy các chủ đề được tìm kiếm nhiều nhất trong 24h qua
            pipeline = [
                {
                    "$match": {
                        "created_at": {
                            "$gte": datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
                        },
                        "topics": {"$exists": True, "$ne": []}
                    }
                },
                {"$unwind": "$topics"},
                {"$group": {"_id": "$topics", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                # {"$limit": limit * 2}  # Lấy gấp đôi để dự phòng
            ]
            
            cursor = self.tasks_collection.aggregate(pipeline)
            popular_topics = []
            
            async for doc in cursor:
                # Kiểm tra xem chủ đề có tồn tại trong results_collection không
                result = await self.results_collection.find_one({"topic": doc["_id"]})
                if result:
                    popular_topics.append(doc["_id"])
                    if len(popular_topics) >= limit:
                        break
            
            return popular_topics[:limit]  # Đảm bảo trả về đúng số lượng yêu cầu
            
        except Exception as e:
            logger.error(f"Error getting popular topics: {str(e)}")
            return []

    async def get_task(self, task_id: str) -> dict:
        """Lấy thông tin task theo ID
        
        Args:
            task_id: ID của task cần lấy
            
        Returns:
            dict: Thông tin task
        """
        try:
            task = await self.tasks_collection.find_one({"_id": ObjectId(task_id)})
            if not task:
                logger.warning(f"Task {task_id} not found")
                return None
            return task
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {str(e)}")
            return None

    async def update_task_status(self, task_id: str, status: str, error: str = None):
        """Cập nhật trạng thái task
        
        Args:
            task_id: ID của task cần cập nhật
            status: Trạng thái mới
            error: Thông tin lỗi (nếu có)
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now(UTC)
            }
            if error:
                update_data["error"] = error

            await self.tasks_collection.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": update_data}
            )
            logger.info(f"Updated task {task_id} status to {status}")
        except Exception as e:
            logger.error(f"Error updating task {task_id} status: {str(e)}")

    async def insert_result(self, task_id: str, topic: str, source: str, language: str, text: str) -> str:
        """Thêm kết quả crawl vào database
        
        Args:
            task_id: ID của task
            topic: Chủ đề
            source: Nguồn dữ liệu
            language: Ngôn ngữ
            text: Nội dung
            
        Returns:
            str: ID của kết quả mới được thêm
        """
        try:
            now = datetime.now(UTC)
            result = {
                "task_id": ObjectId(task_id),
                "topic": topic,
                "source": source,
                "language": language,
                "text": text,
                "created_at": now,
                "updated_at": now
            }
            
            result = await self.results_collection.insert_one(result)
            result_id = str(result.inserted_id)
            
            # Cập nhật result_ids trong task
            await self.tasks_collection.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$push": {"result_ids": result_id},
                    "$set": {"updated_at": now}
                }
            )
            
            logger.info(f"Inserted result for task {task_id}")
            return result_id
        except Exception as e:
            logger.error(f"Error inserting result for task {task_id}: {str(e)}")
            return None

    async def update_result(self, result_id: str, text: str) -> bool:
        """Cập nhật nội dung kết quả
        
        Args:
            result_id: ID của kết quả cần cập nhật
            text: Nội dung mới
            
        Returns:
            bool: True nếu cập nhật thành công
        """
        try:
            now = datetime.now(UTC)
            result = await self.results_collection.update_one(
                {"_id": ObjectId(result_id)},
                {
                    "$set": {
                        "text": text,
                        "updated_at": now
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated result {result_id}")
                return True
            else:
                logger.warning(f"Result {result_id} not found for update")
                return False
        except Exception as e:
            logger.error(f"Error updating result {result_id}: {str(e)}")
            return False

    async def get_result(self, result_id: str) -> dict:
        """Lấy thông tin kết quả theo ID
        
        Args:
            result_id: ID của kết quả cần lấy
            
        Returns:
            dict: Thông tin kết quả
        """
        try:
            result = await self.results_collection.find_one({"_id": ObjectId(result_id)})
            if not result:
                logger.warning(f"Result {result_id} not found")
                return None
            return result
        except Exception as e:
            logger.error(f"Error getting result {result_id}: {str(e)}")
            return None 