import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Thêm thư mục gốc vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

load_dotenv()

async def create_indexes():
    # Kết nối MongoDB
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.data_management
    
    # Tạo index cho tasks collection
    tasks_collection = db.tasks
    # Index cho topics (để tìm kiếm theo chủ đề)
    await tasks_collection.create_index("topics")
    # Index cho created_at (để sắp xếp theo thời gian)
    await tasks_collection.create_index("created_at")
    print("Created indexes for tasks collection")
    
    # Tạo index cho results collection
    results_collection = db.results
    # Index cho task_id (để tìm kiếm kết quả theo task)
    await results_collection.create_index("task_id")
    # Index cho topic (để tìm kiếm theo chủ đề)
    await results_collection.create_index("topic")
    # Index cho created_at (để sắp xếp theo thời gian)
    await results_collection.create_index("created_at")
    print("Created indexes for results collection")

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_indexes()) 