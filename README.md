# Data Crawling and Management System

Hệ thống thu thập và quản lý dữ liệu tự động từ nhiều nguồn khác nhau.

## Tính năng

- Crawl dữ liệu từ nhiều nguồn khác nhau
- Trích xuất chủ đề tự động bằng Gemini AI
- Lưu trữ dữ liệu trong MongoDB
- Cache dữ liệu phổ biến trong Redis
- API RESTful để quản lý và truy xuất dữ liệu

## Cài đặt

1. Clone repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Tạo file `.env` với các biến môi trường:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
REDIS_HOST=redis://<username>:<password>@<host>:<port>
GOOGLE_API_KEY=<your-gemini-api-key>
```

4. Tạo indexes cho MongoDB:
```bash
python -m app.scripts.create_indexes
```

5. Khởi động service cập nhật Redis:
```bash
python -m app.scripts.update_redis
```

6. Khởi động server:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Crawl dữ liệu
- **POST** `/data/crawl`
  - Request body:
    ```json
    {
      "topic": "chủ đề cần crawl",
      "sources": ["nguồn 1", "nguồn 2"],
      "language": "vi"
    }
    ```

### Kiểm tra trạng thái crawl
- **GET** `/data/status/{taskId}`
  - Response:
    ```json
    {
      "taskId": "task_id",
      "status": "completed",
      "resultIds": ["result_id_1", "result_id_2"]
    }
    ```

### Lấy dữ liệu đã crawl
- **GET** `/data/result/{resultId}`
  - Response:
    ```json
    {
      "resultId": "result_id",
      "topic": "chủ đề",
      "source": "nguồn",
      "language": "vi",
      "text": "nội dung"
    }
    ```

### Gợi ý chủ đề phổ biến
- **GET** `/data/suggestions`
  - Response:
    ```json
    [
      "chủ đề 1",
      "chủ đề 2",
      "chủ đề 3"
    ]
    ```

## Cấu trúc dự án

```
app/
├── controllers/
│   └── data_controller.py
├── models/
│   ├── task.py
│   └── result.py
├── services/
│   ├── crawler.py
│   ├── gemini_service.py
│   └── redis_service.py
├── scripts/
│   ├── create_indexes.py
│   └── update_redis.py
└── main.py
```

## Công nghệ sử dụng

- FastAPI: Framework web
- MongoDB: Database chính
- Redis: Cache dữ liệu phổ biến
- Gemini AI: Trích xuất chủ đề
- Motor: Async MongoDB driver
- Redis-py: Redis client
- Uvicorn: ASGI server

## License

MIT License - xem [LICENSE](LICENSE) để biết thêm chi tiết