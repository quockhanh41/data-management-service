from fastapi import FastAPI
from app.controllers.data_controller import router as data_router
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.services.rabbitmq_service import RabbitMQService
import asyncio
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Khởi tạo RabbitMQ service
rabbitmq_service = RabbitMQService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler cho FastAPI app"""
    try:
        # Khởi tạo kết nối RabbitMQ
        await rabbitmq_service.connect()
        logger.info("Connected to RabbitMQ")
        
        # Bắt đầu tiêu thụ tasks trong background
        from app.controllers.data_controller import process_crawl_task
        task = asyncio.create_task(rabbitmq_service.consume_crawl_tasks(process_crawl_task))
        
        yield  # App đang chạy
        
        # Cleanup khi shutdown
        task.cancel()
        await rabbitmq_service.close()
        logger.info("Disconnected from RabbitMQ")
    except Exception as e:
        logger.error(f"Error in lifespan: {str(e)}")
        raise

app = FastAPI(
    title="Data Management Service",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 3000)),
        reload=True
    ) 