import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from bson import Binary
from dotenv import load_dotenv

# Thêm thư mục gốc vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

load_dotenv()

async def create_indexes():
    # Kết nối MongoDB
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"), uuidRepresentation='standard')
    db = client.data_management
    
    # Tạo index cho tasks collection
    tasks_collection = db.tasks
    await tasks_collection.create_index("task_id", unique=True)
    await tasks_collection.create_index("topics")
    await tasks_collection.create_index("created_at")
    print("Created indexes for tasks collection")
    
    # Tạo index cho results collection
    results_collection = db.results
    await results_collection.create_index("result_id", unique=True)
    await results_collection.create_index("task_id")
    await results_collection.create_index("topic")
    await results_collection.create_index("created_at")
    print("Created indexes for results collection")

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_indexes()) 