# 🔄 ChromaDB Migration Guide

## Tổng quan

Dự án đã được refactor từ **Pinecone** sang **ChromaDB**. Đây là những thay đổi chính:

### ✅ Thay đổi

| Component | Trước (Pinecone) | Sau (ChromaDB) |
|-----------|------------------|----------------|
| **Vector Database** | Pinecone (cloud) | ChromaDB (local) |
| **Embeddings** | PineconeEmbeddings | HuggingFaceEmbeddings |
| **Model** | multilingual-e5-large | multilingual-e5-large (same) |
| **API Key** | Cần PINECONE_API_KEY | Không cần! |
| **Storage** | Cloud | Local (thư mục `chroma_db/`) |
| **LLM** | Groq AI (Llama 3.3) | Groq AI (Llama 3.3) - no change |
| **Framework** | LangChain | LangChain - no change |

### 🎯 Lợi ích của ChromaDB

1. **Miễn phí 100%**: Không cần API key, không giới hạn số lượng vectors
2. **Privacy**: Dữ liệu lưu local, không gửi lên cloud
3. **Tốc độ**: Nhanh với dữ liệu nhỏ-trung bình
4. **Đơn giản**: Setup dễ dàng hơn, không cần config cloud

### ⚠️ Trade-offs

1. **Scale**: Phù hợp cho <1M vectors. Nếu cần scale lớn hơn, dùng Pinecone/Qdrant
2. **Distributed**: Không hỗ trợ multi-node deployment
3. **Backup**: Cần tự backup thư mục `chroma_db/`

## 🚀 Hướng dẫn Migration

### Bước 1: Xóa Pinecone dependencies cũ (optional)

```bash
pip uninstall pinecone pinecone-client langchain-pinecone -y
```

### Bước 2: Cài đặt ChromaDB dependencies

```bash
pip install -r requirements.txt
```

Sẽ cài:
- `chromadb>=0.4.22`
- `langchain-chroma>=0.1.0`
- `sentence-transformers>=2.2.0`

### Bước 3: Xóa API key Pinecone trong .env

```bash
# File .env - XÓA dòng này:
# PINECONE_API_KEY=...

# Chỉ cần giữ:
GROQ_API_KEY=your-groq-api-key-here
```

### Bước 4: Xóa Pinecone index cũ (optional)

Pinecone index trên cloud không tự động xóa. Nếu không dùng nữa:
1. Truy cập: https://app.pinecone.io/
2. Xóa index `vietnamese-support-index`

### Bước 5: Tạo ChromaDB collection mới

```bash
python setup.py
```

Lần đầu sẽ:
- Tải model `multilingual-e5-large` (~1.5GB)
- Đọc data từ `data/traning.json`
- Tạo embeddings và lưu vào `chroma_db/`

**Thời gian**: ~3-5 phút lần đầu

### Bước 6: Test chatbot

```bash
# Web UI
streamlit run app.py

# Hoặc Terminal
python vietnamese_chatbot.py
```

## 📁 Cấu trúc thư mục

```
AI_Master_Hackathon/
├── chroma_db/                          # ← NEW: ChromaDB storage (local)
│   └── vietnamese_support_collection/
│       ├── chroma.sqlite3              # Vector database
│       └── ...
├── rag_system/
│   ├── vector_store.py                 # ← REFACTORED: ChromaDB implementation
│   ├── rag_chain.py                    # ← UPDATED: Logging messages
│   └── ...
├── requirements.txt                    # ← UPDATED: ChromaDB dependencies
├── setup.py                            # ← UPDATED: ChromaDB setup
├── README.md                           # ← UPDATED: ChromaDB docs
└── ...
```

## 🔧 Code Changes

### vector_store.py

**Before:**
```python
from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore
from pinecone import Pinecone

self.embeddings = PineconeEmbeddings(model="multilingual-e5-large")
self.pc = Pinecone(api_key=api_key)
```

**After:**
```python
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

self.embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
```

### setup.py

**Before:**
```python
vector_store = VectorStore("vietnamese_support")
vector_store.create_index(chunked_documents)  # Upload to Pinecone cloud
```

**After:**
```python
vector_store = VectorStore("vietnamese_support")
vector_store.create_index(chunked_documents)  # Save to local ChromaDB
```

## 🐛 Troubleshooting

### Lỗi: "No module named 'chromadb'"

```bash
pip install chromadb langchain-chroma sentence-transformers
```

### Lỗi: "Cannot download model"

**Nguyên nhân**: Không có internet hoặc HuggingFace bị block

**Giải pháp**:
1. Kiểm tra internet
2. Nếu ở VN, có thể cần VPN để tải model lần đầu
3. Sau khi tải xong, chạy offline được

### Lỗi: "Collection already exists"

**Giải pháp**: Xóa và tạo lại
```bash
rm -rf chroma_db/
python setup.py
```

### Performance chậm

**Kiểm tra**:
1. Model đã tải xong chưa? (check `~/.cache/huggingface/`)
2. CPU/RAM đủ không? (cần ít nhất 3GB RAM)
3. Có thể dùng GPU: `model_kwargs={'device': 'cuda'}`

## 📊 So sánh Performance

### Pinecone
- Setup time: ~30s (không tải model)
- Query time: ~200-500ms (network latency)
- Storage: Cloud (unlimited)

### ChromaDB
- Setup time: ~3-5 phút lần đầu (tải model), sau đó <5s
- Query time: ~50-100ms (local, no network)
- Storage: Local (~500MB cho 7 sản phẩm)

## 🔐 Data Privacy

### Pinecone
- Data lưu trên cloud (AWS/GCP)
- Embeddings gửi qua API
- Phụ thuộc vào Pinecone infrastructure

### ChromaDB
- ✅ 100% local, không gửi data đi đâu
- ✅ Embeddings tạo trên máy của bạn
- ✅ Phù hợp cho dữ liệu y tế, tài chính

## 🎓 Best Practices

### Development
- ✅ Dùng ChromaDB (free, local, easy)
- ✅ Test trên máy local
- ✅ Prototype nhanh

### Production (Small Scale)
- ✅ ChromaDB vẫn OK cho <100k vectors
- ✅ Backup thư mục `chroma_db/` thường xuyên
- ✅ Monitor disk space

### Production (Large Scale)
- ⚠️ Cân nhắc Pinecone/Qdrant/Weaviate
- ⚠️ Cần distributed setup
- ⚠️ Cần managed backup/recovery

## 📚 Resources

- [ChromaDB Docs](https://docs.trychroma.com/)
- [LangChain ChromaDB Integration](https://python.langchain.com/docs/integrations/vectorstores/chroma)
- [HuggingFace Embeddings](https://huggingface.co/intfloat/multilingual-e5-large)
- [Groq AI](https://console.groq.com/docs)

## ✅ Migration Checklist

- [ ] Xóa Pinecone dependencies: `pip uninstall pinecone -y`
- [ ] Cài ChromaDB: `pip install -r requirements.txt`
- [ ] Xóa `PINECONE_API_KEY` trong `.env`
- [ ] Chạy `python setup.py`
- [ ] Test chatbot: `streamlit run app.py`
- [ ] Verify: Hỏi "The Fucoidan là gì?"
- [ ] (Optional) Xóa Pinecone index trên cloud

## 🤝 Support

Nếu gặp vấn đề:
1. Kiểm tra lại README.md
2. Xem Troubleshooting section
3. Create issue trên GitHub

---

**Happy coding!** 🎉
