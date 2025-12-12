# 🐳 Hướng dẫn Deploy ChatBot AI Tâm Quốc Tế với Docker

## 📋 Yêu cầu

- Docker và Docker Compose đã được cài đặt
- API keys: GROQ_API_KEY và PINECONE_API_KEY

## 🚀 Cách Deploy

### Bước 1: Chuẩn bị Environment Variables

Tạo file `.env` từ template:

```bash
cp .docker.env.example .env
```

Sau đó chỉnh sửa file `.env` và thêm API keys của bạn:

```env
GROQ_API_KEY=your-groq-api-key-here
PINECONE_API_KEY=your-pinecone-api-key-here
```

### Bước 2: Build và Chạy với Docker Compose

```bash
# Build và chạy container
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng container
docker-compose down
```

### Bước 3: Truy cập ứng dụng

Mở browser và truy cập: `http://localhost:8501`

## 🔧 Các lệnh Docker hữu ích

### Build image riêng lẻ

```bash
docker build -t chatbot-tam-quoc-te:latest .
```

### Chạy container riêng lẻ

```bash
docker run -d \
  --name chatbot-tam-quoc-te \
  -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/data:/app/data:ro \
  -v $(pwd)/conversation_memory:/app/conversation_memory \
  chatbot-tam-quoc-te:latest
```

### Xem logs

```bash
# Với docker-compose
docker-compose logs -f

# Với docker run
docker logs -f chatbot-tam-quoc-te
```

### Vào trong container

```bash
docker exec -it chatbot-tam-quoc-te /bin/bash
```

### Rebuild sau khi thay đổi code

```bash
docker-compose up -d --build
```

## 📁 Cấu trúc Volumes

- `./data:/app/data:ro` - Mount thư mục data (read-only) để đọc file Excel/JSON
- `./conversation_memory:/app/conversation_memory` - Lưu lịch sử chat

## 🔄 Cập nhật dữ liệu

Để cập nhật dữ liệu trong file Excel/JSON:

1. Cập nhật file trong thư mục `data/` trên host
2. Restart container để load dữ liệu mới:

```bash
docker-compose restart
```

Hoặc nếu cần recreate index:

```bash
docker exec -it chatbot-tam-quoc-te python rag_system/pinecone/recreate_index.py
```

## 🐛 Troubleshooting

### Container không start

```bash
# Kiểm tra logs
docker-compose logs chatbot

# Kiểm tra environment variables
docker-compose config
```

### Lỗi "API key not found"

Đảm bảo file `.env` tồn tại và có đầy đủ API keys:

```bash
cat .env
```

### Port đã được sử dụng

Thay đổi port trong `docker-compose.yml`:

```yaml
ports:
  - "8502:8501"  # Thay 8501 thành 8502
```

## 🌐 Deploy lên Production

### Với Docker Swarm

```bash
docker stack deploy -c docker-compose.yml chatbot
```

### Với Kubernetes

Cần tạo thêm:
- `k8s/deployment.yaml`
- `k8s/service.yaml`
- `k8s/configmap.yaml` (cho env vars)

### Với Cloud Platforms

- **AWS**: Sử dụng ECS hoặc EKS
- **Google Cloud**: Sử dụng Cloud Run hoặc GKE
- **Azure**: Sử dụng Container Instances hoặc AKS
- **DigitalOcean**: Sử dụng App Platform hoặc Droplets

## 📝 Notes

- Container tự động restart nếu crash (`restart: unless-stopped`)
- Health check được cấu hình để monitor container
- Data files được mount read-only để bảo vệ dữ liệu gốc
- Conversation memory được lưu trên host để persist giữa các lần restart

