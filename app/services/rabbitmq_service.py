import aio_pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

class RabbitMQService:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None
        self._is_connected = False

    async def ensure_connection(self):
        """Đảm bảo kết nối RabbitMQ đã được thiết lập"""
        if not self._is_connected:
            await self.connect()

    async def connect(self):
        """Kết nối đến RabbitMQ server"""
        try:
            self.connection = await aio_pika.connect_robust(
                os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
            )
            self.channel = await self.connection.channel()
            self.queue = await self.channel.declare_queue("crawl_queue", durable=True)
            self._is_connected = True
            print("Connected to RabbitMQ successfully")
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def close(self):
        """Đóng kết nối RabbitMQ"""
        if self.connection:
            await self.connection.close()
            self._is_connected = False
            self.connection = None
            self.channel = None
            self.queue = None

    async def publish_crawl_task(self, task_id: str, data: dict):
        """Gửi task crawl vào queue"""
        await self.ensure_connection()
        
        message = {
            "task_id": task_id,
            "data": data
        }
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="crawl_queue"
        )

    async def consume_crawl_tasks(self, callback):
        """Tiêu thụ các task crawl từ queue"""
        await self.ensure_connection()
        
        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        await callback(data)
                    except Exception as e:
                        print(f"Error processing message: {str(e)}") 