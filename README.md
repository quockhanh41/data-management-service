# Data Management Service

Dịch vụ quản lý và thu thập dữ liệu tự động từ nhiều nguồn khác nhau.

## Tính năng

- Trích xuất chủ đề từ input người dùng sử dụng Gemini AI
- Thu thập dữ liệu từ nhiều nguồn khác nhau
- Xử lý bất đồng bộ các task crawl
- Lưu trữ và quản lý kết quả trong MongoDB
- API RESTful để tương tác với hệ thống

## Công nghệ sử dụng

- FastAPI: Framework web hiệu suất cao
- MongoDB: Cơ sở dữ liệu NoSQL
- RabbitMQ: Message broker cho xử lý bất đồng bộ
- Gemini AI: Xử lý ngôn ngữ tự nhiên
- Redis: Caching và lưu trữ tạm thời

## Cài đặt

1. Clone repository:
```bash
git clone <repository-url>
cd data-management-service
```

2. Tạo và kích hoạt môi trường ảo:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Tạo file `.env` và cấu hình các biến môi trường:
```env
MONGODB_URI=mongodb://localhost:27017
RABBITMQ_URL=amqp://guest:guest@localhost/
GEMINI_API_KEY=your_gemini_api_key
PORT=3000
```

## Cấu trúc dự án

```
.
├── app/
│   ├── controllers/     # Xử lý request API
│   ├── models/         # Định nghĩa dữ liệu
│   ├── services/       # Các dịch vụ
│   └── __init__.py
├── main.py            # Điểm khởi đầu ứng dụng
├── requirements.txt   # Các dependencies
└── README.md         # Tài liệu
```

## API Endpoints

### 1. Trích xuất và crawl dữ liệu

```http
POST /api/v1/data/crawl
```

Request body:
```json
{
    "topic": "chủ đề cần tìm hiểu",
    "sources": ["wikipedia", "pubmed"],
    "language": "vi"
}
```

Response:
```json
{
    "message": "Đang tiến hành crawl dữ liệu...",
    "taskId": "task_id",
    "extractedTopics": ["chủ đề 1", "chủ đề 2"]
}
```

### 2. Kiểm tra trạng thái task

```http
GET /api/v1/data/status/{task_id}
```

Response:
```json
{
    "taskId": "task_id",
    "status": "completed",
    "resultIds": ["result_id_1", "result_id_2"]
}
```

### 3. Lấy kết quả crawl

```http
GET /api/v1/data/result/{result_id}
```

Response:
```json
{
    "resultId": "result_id",
    "topic": "chủ đề",
    "source": "nguồn",
    "language": "vi",
    "text": "nội dung"
}
```

### 4. Lấy các chủ đề phổ biến

```http
GET /api/v1/data/popular-topics
```

Response:
```json
["chủ đề 1", "chủ đề 2", "chủ đề 3"]
```

## Chạy ứng dụng

1. Khởi động server:
```bash
python main.py
```

2. Chạy consumer để xử lý tasks:
```bash
python consume_messages.py
```

## Quy trình xử lý

1. Người dùng gửi request crawl với chủ đề
2. Gemini AI trích xuất các chủ đề con
3. Tạo task mới và gửi vào RabbitMQ queue
4. Consumer nhận task và thực hiện crawl
5. Lưu kết quả vào MongoDB
6. Người dùng có thể kiểm tra trạng thái và lấy kết quả

## Xử lý lỗi

- Các lỗi được ghi log chi tiết
- Tasks thất bại được đánh dấu và lưu thông tin lỗi
- Có thể retry các tasks thất bại

## Bảo mật

- CORS được cấu hình để cho phép truy cập từ nhiều nguồn
- API keys được lưu trong biến môi trường
- Dữ liệu nhạy cảm được mã hóa

## Đóng góp

1. Fork repository
2. Tạo branch mới
3. Commit changes
4. Push lên branch
5. Tạo Pull Request

## Giấy phép

MIT License