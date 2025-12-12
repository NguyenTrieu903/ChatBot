#!/bin/bash
# Script helper để chạy Docker container

set -e

echo "🐳 ChatBot AI Tâm Quốc Tế - Docker Deployment"
echo "=============================================="

# Kiểm tra .env file
if [ ! -f .env ]; then
    echo "⚠️  File .env không tồn tại!"
    echo "📝 Đang tạo file .env từ template..."
    if [ -f .docker.env.example ]; then
        cp .docker.env.example .env
        echo "✅ Đã tạo file .env"
        echo "⚠️  VUI LÒNG CHỈNH SỬA file .env và thêm API keys của bạn!"
        exit 1
    else
        echo "❌ Không tìm thấy .docker.env.example"
        exit 1
    fi
fi

# Kiểm tra API keys
if ! grep -q "GROQ_API_KEY=.*[^=]$" .env || ! grep -q "PINECONE_API_KEY=.*[^=]$" .env; then
    echo "⚠️  API keys chưa được cấu hình trong .env"
    echo "📝 Vui lòng chỉnh sửa file .env và thêm API keys"
    exit 1
fi

# Build và chạy
echo ""
echo "🔨 Đang build Docker image..."
docker compose build

echo ""
echo "🚀 Đang khởi động container..."
docker compose up -d

echo ""
echo "⏳ Đợi container khởi động..."
sleep 5

# Kiểm tra container
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Container đã khởi động thành công!"
    echo ""
    echo "📊 Xem logs:"
    echo "   docker compose logs -f"
    echo ""
    echo "🌐 Truy cập ứng dụng:"
    echo "   http://localhost:8501"
    echo ""
    echo "🛑 Dừng container:"
    echo "   docker-compose down"
else
    echo "❌ Container không khởi động được"
    echo "📋 Xem logs để biết lỗi:"
    echo "   docker-compose logs"
    exit 1
fi

