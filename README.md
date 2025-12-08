# ⚡ HƯỚNG DẪN NHANH - 5 PHÚT

## 🎯 Bắt đầu ngay với Groq AI (Free & Fast!)

### Bước 1: Lấy Groq API Key miễn phí (30 giây)

1. Mở: https://console.groq.com/keys
2. Sign up/Login (miễn phí, không cần thẻ)
3. Click **"Create API Key"**
4. Copy API key

**Groq Free Tier:**
- ✅ 14,400 requests/day (Gemini chỉ 20!)
- ✅ 30 requests/minute
- ✅ Cực nhanh (<500ms)
- ✅ Llama 3.3 70B model

### Bước 2: Cài đặt (3-5 phút)

```bash
# Kích hoạt conda environment
conda activate py310

# Vào thư mục
cd D:\projects\AI_Master_Hackathon\AI_Master_Hackathon

# Cài thư viện (lần đầu sẽ tải model embedding ~120MB)
pip install -r requirements.txt

# Tạo file .env với API key
echo GROQ_API_KEY=your-api-key-here > .env
echo PINECONE_API_KEY=your-pinecone-api-key-here > .env

# Chạy setup (lần đầu mất 2-3 phút để tải embedding model)
python setup.py
```

**Lưu ý:** Lần đầu chạy sẽ tải model embedding (~120MB). Sau đó chạy nhanh!

### Bước 3: Chạy chatbot

#### 🎨 Web UI (Khuyên dùng)

```bash
streamlit run app.py

# Hoặc
./run_ui.sh    # Linux/WSL
run_ui.bat     # Windows
```

Mở browser: `http://localhost:8501`

#### 💻 Terminal (Đơn giản)

```bash
python vietnamese_chatbot.py
```

## ✅ Xong! Bắt đầu chat

**Web UI:**
- Giao diện đẹp, dễ dùng
- Hiển thị nguồn tài liệu
- Export chat history
- Thống kê real-time

**Terminal:**
```
👤 Bạn: Xin chào
🤖 Bot: Xin chào! Tôi có thể giúp gì cho bạn?
```

## 🆘 Gặp lỗi?

### Lỗi: "GROQ_API_KEY not found"

**Tạo file `.env`:**
```bash
echo GROQ_API_KEY=your-api-key > .env
```

Hoặc tạo file `.env` bằng notepad với nội dung:
```
GROQ_API_KEY=your-api-key-here
```

**Lấy key tại:** https://console.groq.com/keys

### Lỗi: "No module named..."

```bash
pip install -r requirements.txt
```

### Lỗi: "File not found: traning.xlsx"

Đảm bảo 2 file này tồn tại:
- `D:\projects\AI_Master_Hackathon\traning.xlsx`
- `D:\projects\AI_Master_Hackathon\Training data.docx`

## 📖 Chi tiết

Xem file `README.md` để biết thêm chi tiết.

---

**🚀 Chỉ 5 phút để có chatbot AI của riêng bạn!**

