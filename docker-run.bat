@echo off
REM Script helper để chạy Docker container trên Windows

echo 🐳 ChatBot AI Tâm Quốc Tế - Docker Deployment
echo ==============================================

REM Kiểm tra .env file
if not exist .env (
    echo ⚠️  File .env không tồn tại!
    echo 📝 Đang tạo file .env từ template...
    if exist .docker.env.example (
        copy .docker.env.example .env
        echo ✅ Đã tạo file .env
        echo ⚠️  VUI LÒNG CHỈNH SỬA file .env và thêm API keys của bạn!
        pause
        exit /b 1
    ) else (
        echo ❌ Không tìm thấy .docker.env.example
        pause
        exit /b 1
    )
)

echo.
echo 🔨 Đang build Docker image...
docker-compose build

echo.
echo 🚀 Đang khởi động container...
docker-compose up -d

echo.
echo ⏳ Đợi container khởi động...
timeout /t 5 /nobreak >nul

REM Kiểm tra container
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo.
    echo ✅ Container đã khởi động thành công!
    echo.
    echo 📊 Xem logs:
    echo    docker-compose logs -f
    echo.
    echo 🌐 Truy cập ứng dụng:
    echo    http://localhost:8501
    echo.
    echo 🛑 Dừng container:
    echo    docker-compose down
) else (
    echo ❌ Container không khởi động được
    echo 📋 Xem logs để biết lỗi:
    echo    docker-compose logs
)

pause

