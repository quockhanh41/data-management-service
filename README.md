# Data Management System

Hệ thống quản lý và crawl dữ liệu từ nhiều nguồn khác nhau.

## Các Service Chính

### 1. Crawler Service
Service chịu trách nhiệm crawl dữ liệu từ các nguồn khác nhau.

#### Các tính năng:
- Crawl dữ liệu từ Wikipedia
- Crawl dữ liệu từ Nature
- Crawl dữ liệu từ PubMed
- Hỗ trợ đa ngôn ngữ
- Caching dữ liệu với Redis
- Lưu trữ dữ liệu vào MongoDB

#### Cách sử dụng:
```python
crawler = Crawler(redis_service, mongodb_service)
results = await crawler.crawl(
    task_id="task_id",
    topic="topic_name",
    sources=["wikipedia", "nature", "pubmed"],
    language="en"
)
```

### 2. MongoDB Service
Service quản lý dữ liệu với MongoDB.

#### Các tính năng:
- Kết nối và quản lý MongoDB
- Lưu trữ tasks và results
- Lấy danh sách chủ đề phổ biến
- Cập nhật trạng thái task
- Quản lý kết quả crawl

#### Các phương thức chính:
- `get_popular_topics(limit=5)`: Lấy danh sách chủ đề phổ biến
- `get_task(task_id)`: Lấy thông tin task
- `update_task_status(task_id, status, error)`: Cập nhật trạng thái task
- `insert_result(task_id, topic, source, language, text)`: Thêm kết quả crawl
- `update_result(result_id, text)`: Cập nhật kết quả
- `get_result(result_id)`: Lấy thông tin kết quả

### 3. Redis Service
Service quản lý cache với Redis.

#### Các tính năng:
- Cache dữ liệu crawl
- TTL (Time To Live) cho cache
- Quản lý kết nối Redis

### 4. RabbitMQ Service
Service quản lý message queue với RabbitMQ.

#### Các tính năng:
- Publish/Subscribe messages
- Quản lý tasks
- Xử lý bất đồng bộ

## Cấu trúc dữ liệu

### Task
```json
{
    "_id": "ObjectId",
    "input_user": "string",
    "topics": ["string"],
    "sources": ["string"],
    "language": "string",
    "status": "string",
    "result_ids": ["string"],
    "created_at": "datetime",
    "updated_at": "datetime",
    "error": "string"
}
```

### Result
```json
{
    "_id": "ObjectId",
    "task_id": "ObjectId",
    "topic": "string",
    "source": "string",
    "language": "string",
    "text": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

## Cài đặt và Chạy

1. Cài đặt các dependencies:
```bash
pip install -r requirements.txt
```

2. Cấu hình biến môi trường:
```bash
export MONGODB_URI="mongodb://localhost:27017"
export REDIS_URL="redis://localhost:6379"
export RABBITMQ_URL="amqp://localhost:5672"
```

3. Chạy service:
```bash
python main.py
```

## Xử lý lỗi

- Tất cả các service đều có logging để theo dõi lỗi
- Các lỗi được xử lý và lưu trữ trong task
- Có cơ chế retry cho các thao tác thất bại

## Best Practices

1. Luôn sử dụng async/await cho các thao tác I/O
2. Sử dụng connection pooling cho database
3. Implement retry mechanism cho các thao tác quan trọng
4. Log đầy đủ thông tin lỗi
5. Sử dụng transaction khi cần atomic operations
6. Validate input data trước khi xử lý
7. Sử dụng environment variables cho cấu hình
8. Implement health check endpoints
9. Sử dụng connection timeout
10. Implement circuit breaker pattern