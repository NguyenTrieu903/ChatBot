# ⚡ Quick Start Guide - 5 Phút

## 🎯 Chatbot Y Tế với ChromaDB + LangChain + Groq AI

### Bước 1: Cài đặt Python environment (1 phút)

```bash
# Đảm bảo đang dùng Python 3.10+
python --version

# Di chuyển vào thư mục project
cd AI_Master_Hackathon
```

### Bước 2: Cài đặt dependencies (2 phút)

```bash
# Cài tất cả thư viện cần thiết
pip install -r requirements.txt
```

**Lưu ý**: Lần đầu sẽ tải embedding model (~1.5GB)

### Bước 3: Lấy Groq API Key (30 giây)

1. Truy cập: https://console.groq.com/keys
2. Sign up/Login (miễn phí!)
3. Click "Create API Key"
4. Copy key

### Bước 4: Tạo file .env (10 giây)

**Windows:**
```cmd
echo GROQ_API_KEY=paste-your-key-here > .env
```

**Linux/Mac:**
```bash
echo "GROQ_API_KEY=paste-your-key-here" > .env
```

**Hoặc dùng text editor:**
- Tạo file `.env` trong thư mục `AI_Master_Hackathon`
- Nội dung:
```
GROQ_API_KEY=your-groq-api-key-here
```

### Bước 5: Setup ChromaDB (3-5 phút lần đầu)

```bash
python setup.py
```

Sẽ:
- ✅ Tải embedding model (lần đầu)
- ✅ Đọc dữ liệu từ `data/traning.json`
- ✅ Tạo ChromaDB collection (local)

### Bước 6: Chạy chatbot! 🚀

**Web UI (Recommended):**
```bash
streamlit run app.py
```
Mở browser: http://localhost:8501

**Terminal:**
```bash
python vietnamese_chatbot.py
```

### Bước 7: Test (optional)

```bash
python test_chromadb.py
```

## 💬 Ví dụ

```
👤 Bạn: The Fucoidan là gì?
🤖 Bot: The Fucoidan là sản phẩm chứa 100% tinh chất Fucoidan 
        chiết xuất từ Tảo nâu Okinawa Mozuku Nhật Bản...

👤 Bạn: Giá bao nhiêu?
🤖 Bot: The Fucoidan có giá 2.200.000₫ cho hộp 90 viên.

👤 Bạn: Liều dùng như thế nào?
🤖 Bot: Liều dùng The Fucoidan:
        • Duy trì: 3 viên/ngày
        • Tăng cường: 6 viên/ngày (2 lần/ngày, mỗi lần 3 viên)
```

## 🐛 Gặp lỗi?

### "GROQ_API_KEY not found"
→ Kiểm tra file `.env` đã tạo đúng chưa

### "No module named 'chromadb'"
→ Chạy: `pip install -r requirements.txt`

### "Collection not found"
→ Chạy: `python setup.py`

### "Cannot download model"
→ Kiểm tra internet. Nếu ở VN, có thể cần VPN lần đầu

## 📚 Chi tiết thêm

- **Full docs**: Xem `README.md`
- **Migration guide**: Xem `CHROMADB_MIGRATION.md`
- **Test**: Chạy `python test_chromadb.py`

## 💡 Ưu điểm

✅ **Miễn phí 100%**: ChromaDB local, không cần API key  
✅ **Privacy**: Dữ liệu lưu local, an toàn  
✅ **Nhanh**: Response <100ms (local query)  
✅ **Đơn giản**: Setup dễ dàng, không cần cloud config  

## 🎉 Done!

Giờ bạn đã có chatbot y tế AI của riêng mình!

**Need help?** Create issue trên GitHub

---

Made with ❤️ by AI Master Hackathon Team
