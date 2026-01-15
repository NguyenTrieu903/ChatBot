# 🏥 Chatbot Y Tế Tiếng Việt - ChromaDB + LangChain + Groq AI

Chatbot AI hỗ trợ tư vấn về sản phẩm y tế, sử dụng công nghệ RAG (Retrieval-Augmented Generation) với:
- **ChromaDB**: Vector database local, miễn phí
- **LangChain**: Framework xây dựng ứng dụng AI
- **Groq AI**: LLM inference cực nhanh (Llama 3.3 70B)
- **HuggingFace Embeddings**: multilingual-e5-large model

## ⚡ Cài đặt nhanh (5-10 phút)

### 1. Yêu cầu hệ thống
- Python 3.10+
- 3GB RAM
- 3GB dung lượng trống (cho embedding model)

### 2. Cài đặt thư viện

```bash
# Kích hoạt Python environment
conda activate py310  # hoặc venv của bạn

# Di chuyển vào thư mục project
cd AI_Master_Hackathon

# Cài đặt dependencies
pip install -r requirements.txt
```

**Lưu ý**: Lần đầu chạy sẽ tải model `multilingual-e5-large` (~1.5GB). Sau đó chạy nhanh!

### 3. Lấy Groq API Key (miễn phí)

1. Truy cập: https://console.groq.com/keys
2. Sign up/Login (miễn phí, không cần thẻ)
3. Click **"Create API Key"**
4. Copy API key

**Groq Free Tier:**
- ✅ 14,400 requests/day
- ✅ 30 requests/minute
- ✅ Cực nhanh (<500ms response)
- ✅ Model Llama 3.3 70B

### 4. Tạo file `.env`

Tạo file `.env` trong thư mục `AI_Master_Hackathon` với nội dung:

```bash
GROQ_API_KEY=your-groq-api-key-here
```

**Windows (Command Prompt):**
```cmd
echo GROQ_API_KEY=your-groq-api-key-here > .env
```

**Linux/Mac:**
```bash
echo "GROQ_API_KEY=your-groq-api-key-here" > .env
```

### 5. Chạy setup (khởi tạo ChromaDB)

```bash
python setup.py
```

Quá trình này sẽ:
- Tải embedding model (~1.5GB) lần đầu
- Đọc dữ liệu từ `data/traning.json`
- Tạo embeddings cho các document
- Lưu vào ChromaDB (local, trong thư mục `chroma_db/`)

**Thời gian**: ~3-5 phút lần đầu, sau đó chỉ vài giây.

### 6. Chạy chatbot

#### 🎨 Web UI (Khuyên dùng)

```bash
streamlit run app.py
```

Mở trình duyệt tại: `http://localhost:8501`

**Tính năng Web UI:**
- ✨ Giao diện đẹp, thân thiện
- 💬 Chat history
- 🔍 Hiển thị nguồn tài liệu
- 📊 Thống kê real-time

#### 💻 Terminal (Đơn giản)

```bash
python vietnamese_chatbot.py
```

## 📊 Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                            │
│              (Streamlit Web UI / Terminal)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Vietnamese Chatbot                            │
│          (vietnamese_chatbot.py)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG Chain                                 │
│            (rag_system/rag_chain.py)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ConversationBufferWindowMemory (k=5)                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                                    │
           ▼                                    ▼
┌──────────────────────────┐      ┌──────────────────────────┐
│   Vector Store           │      │      LLM (Groq AI)       │
│  (ChromaDB - Local)      │      │  Llama 3.3 70B Model     │
│                          │      │                          │
│  HuggingFace Embeddings  │      │  Temperature: 0.7        │
│  multilingual-e5-large   │      │  Max tokens: 8000        │
└──────────────────────────┘      └──────────────────────────┘
```

### Flow hoạt động:

1. **User Input** → Câu hỏi từ người dùng
2. **Embedding** → Chuyển câu hỏi thành vector (multilingual-e5-large)
3. **ChromaDB Retrieval** → Tìm kiếm top-k documents tương tự (cosine similarity)
4. **Context Formation** → Kết hợp documents thành context
5. **LLM Generation** → Groq AI (Llama 3.3 70B) tạo câu trả lời
6. **Memory Update** → Lưu conversation history (k=5 exchanges)

## 🗂️ Cấu trúc dữ liệu

File `data/traning.json` chứa thông tin sản phẩm y tế:

```json
[
  {
    "name": "Tên sản phẩm",
    "metadata": "Mô tả chi tiết về sản phẩm, công dụng, liều dùng, giá..."
  }
]
```

**Các sản phẩm hiện có:**
- The Fucoidan (hỗ trợ ung thư)
- The Fucoidan xK (phiên bản nâng cấp)
- β-Glucan Ball (chiết xuất nấm)
- Kidney & Men's (bổ thận nam giới)
- Power HLP (phòng ngừa đột quỵ)
- The Reishi (Linh Chi + Agaricus)
- Paracetamol (giảm đau, hạ sốt)

## 💡 Ví dụ sử dụng

```
👤 User: The Fucoidan là gì?
🤖 Bot: The Fucoidan là sản phẩm chứa 100% tinh chất Fucoidan chiết xuất từ 
        Tảo nâu Okinawa Mozuku Nhật Bản với hàm lượng cao 200mg/viên...

👤 User: Giá bao nhiêu?
🤖 Bot: The Fucoidan có giá 2.200.000₫ cho hộp 90 viên...

👤 User: Liều dùng như thế nào?
🤖 Bot: Liều dùng The Fucoidan:
        - Duy trì: 3 viên/ngày
        - Tăng cường: 6 viên/ngày (2 lần/ngày, mỗi lần 3 viên)
```

## 🔧 Cấu hình nâng cao

### Tùy chỉnh Chunking

File `data_loader.py`:

```python
def load_and_chunk_json(
    json_file: str,
    chunk_size: int = 1000,     # Kích thước chunk
    chunk_overlap: int = 200     # Độ overlap giữa chunks
)
```

### Tùy chỉnh Retrieval

File `rag_system/rag_chain.py`:

```python
self.retriever = self.vector_store.get_retriever(
    k=5,                      # Số documents trả về
    score_threshold=None      # Ngưỡng similarity (None = không giới hạn)
)
```

### Tùy chỉnh LLM

File `rag_system/rag_chain.py`:

```python
ChatGroq(
    model="llama-3.3-70b-versatile",  # Model name
    temperature=0.7,                   # Độ sáng tạo (0-1)
    max_tokens=8000                    # Độ dài response
)
```

### Tùy chỉnh Memory

```python
ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    k=5  # Giữ 5 exchanges gần nhất
)
```

## 🆚 So sánh với Pinecone

| Tính năng | ChromaDB | Pinecone |
|-----------|----------|----------|
| **Giá** | Miễn phí 100% | Free tier có giới hạn |
| **Vị trí** | Local | Cloud |
| **API Key** | Không cần | Cần |
| **Tốc độ** | Nhanh (local) | Nhanh (tối ưu cho scale) |
| **Scale** | Tốt cho small-medium | Tốt cho large scale |
| **Privacy** | Cao (local) | Phụ thuộc cloud |
| **Setup** | Đơn giản | Cần API key |

**Khi nào dùng ChromaDB:**
- ✅ Prototype/Development
- ✅ Dữ liệu nhạy cảm (y tế, tài chính)
- ✅ Budget hạn chế
- ✅ Dữ liệu nhỏ-trung bình (<1M vectors)

**Khi nào dùng Pinecone:**
- ✅ Production scale lớn (>1M vectors)
- ✅ Multi-region deployment
- ✅ Cần managed service
- ✅ Team collaboration

## 🐛 Troubleshooting

### Lỗi: "GROQ_API_KEY not found"

**Giải pháp:**
```bash
# Kiểm tra file .env
cat .env

# Nếu không có, tạo file .env
echo "GROQ_API_KEY=your-key-here" > .env
```

### Lỗi: "No module named 'chromadb'"

**Giải pháp:**
```bash
pip install -r requirements.txt
```

### Lỗi: "Cannot download model"

**Nguyên nhân:** Không có internet hoặc HuggingFace bị block

**Giải pháp:**
1. Kiểm tra kết nối internet
2. Nếu ở Việt Nam, có thể cần VPN để tải model lần đầu
3. Sau khi tải xong, chạy offline được

### Lỗi: "Collection not found"

**Giải pháp:**
```bash
# Xóa database cũ và tạo lại
rm -rf chroma_db/
python setup.py
```

### Chatbot trả lời không chính xác

**Kiểm tra:**
1. Dữ liệu trong `data/traning.json` đầy đủ chưa?
2. Đã chạy `python setup.py` sau khi cập nhật dữ liệu?
3. Tăng số documents retrieve: `k=10` trong `get_retriever()`

## 📝 Thêm dữ liệu mới

1. **Cập nhật file JSON:**

```json
{
  "name": "Sản phẩm mới",
  "metadata": "Mô tả chi tiết..."
}
```

2. **Xóa ChromaDB cũ và tạo lại:**

```bash
rm -rf chroma_db/
python setup.py
```

3. **Khởi động lại chatbot:**

```bash
streamlit run app.py
```

## 🚀 Deploy Production

### Option 1: Docker (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python setup.py

CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

### Option 2: VPS (Ubuntu)

```bash
# Install dependencies
sudo apt update
sudo apt install python3.10 python3-pip

# Clone project
git clone <your-repo>
cd AI_Master_Hackathon

# Setup
pip install -r requirements.txt
python setup.py

# Run with systemd or screen
screen -S chatbot
streamlit run app.py --server.port 8501
```

## 📚 Tài liệu tham khảo

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Groq AI Documentation](https://console.groq.com/docs)
- [HuggingFace Embeddings](https://huggingface.co/intfloat/multilingual-e5-large)

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng:
1. Fork repo
2. Tạo branch mới
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License - Feel free to use for your projects!

## 👨‍💻 Tác giả

AI Master Hackathon Team

---

**🎉 Chúc bạn xây dựng chatbot thành công!**

Nếu có câu hỏi, vui lòng tạo issue trên GitHub.