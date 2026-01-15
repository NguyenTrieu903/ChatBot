# 🏥 Vietnamese Medical Chatbot

AI chatbot for medical product consultation using **ChromaDB + LangChain + Groq AI**.

⚠️ **MEDICAL-GRADE SAFETY:** This chatbot implements strict safety controls to prevent hallucination and ensure medical information accuracy. See [SAFETY_IMPROVEMENTS.md](SAFETY_IMPROVEMENTS.md) for details.

## ✨ Features

### Core Technology
- 🤖 **Groq AI** - Fast LLM inference (Llama 3.3 70B, free tier)
- 🗄️ **ChromaDB** - Local vector database (no API key needed!)
- 🔗 **LangChain** - RAG implementation with conversation memory
- 🇻🇳 **Vietnamese Support** - Multilingual embeddings (multilingual-e5-large)
- 💬 **Chat History** - Remembers last 5 conversation exchanges
- 🎨 **Beautiful UI** - Streamlit web interface

### 🛡️ Medical Safety Features
- 🚫 **Anti-Hallucination** - Strict prompt engineering, only answers from database
- 📊 **Score Threshold** - Filters irrelevant context (similarity ≥ 0.7)
- 📚 **Citation Required** - Every answer includes sources
- 🏥 **Question Classifier** - Blocks medical diagnosis/prescription questions
- ⚠️ **Hard Fallback** - Never guesses when data is insufficient
- 🔒 **Safety Layer** - Multi-layer protection against medical misinformation
- 📋 **Structured Data** - Medical fields parsing for better accuracy

### ✨ Vietnamese Text Normalization (NEW!)
- 🇻🇳 **Auto-Normalize** - Converts text without diacritics to proper Vietnamese
  - Input: "gia bao nhieu" → Normalized: "giá bao nhiêu"
  - Input: "thuoc bo than" → Normalized: "thuốc bổ thận"
- 🤖 **LLM-Powered** - Uses Groq Llama 3.3 for intelligent normalization
- 🎯 **Context-Aware** - Understands Vietnamese grammar and context
- 📝 **Spell Check** - Fixes common typos automatically
- ⚡ **Fast** - ~100-300ms latency, worth it for better UX
- 🛡️ **Safe Fallback** - Uses original input if normalization fails

**Benefit:** Users can type naturally without diacritics (faster, easier on mobile)

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies

```bash
cd AI_Master_Hackathon
pip install -r requirements.txt
```

**Note:** First run will download embedding model (~1.5GB). After that, everything runs fast!

### 2. Setup API Key

Get your **free** Groq API key:
1. Visit: https://console.groq.com/keys
2. Sign up (free, no credit card required)
3. Create an API key

Create a `.env` file in the `AI_Master_Hackathon` folder:

```bash
GROQ_API_KEY=your-groq-api-key-here
```

**Quick way:**
```bash
# Copy template
cp env.template .env

# Edit .env and add your API key
```

### 3. Run the App

```bash
streamlit run app.py
```

That's it! 🎉

The app will:
- ✅ Auto-initialize ChromaDB on first run
- ✅ Load medical data from `data/traning.json`
- ✅ Create embeddings and vector index
- ✅ Start the web interface at `http://localhost:8501`

## 📊 Architecture

```
User → Streamlit UI → RAG Chain
                         ↓
               ┌─────────┴─────────┐
               ↓                   ↓
         ChromaDB              Groq AI
    (HuggingFace E5)      (Llama 3.3 70B)
```

### How it works:

1. **User Question** → Embedded using multilingual-e5-large
2. **ChromaDB** → Retrieves top 5 relevant documents
3. **Context Formation** → Combines documents with chat history
4. **Groq AI** → Generates answer using Llama 3.3 70B
5. **Memory** → Saves conversation for context

## 📁 Project Structure

```
AI_Master_Hackathon/
├── app.py                       # Streamlit web UI (auto-init ChromaDB)
├── requirements.txt             # Python dependencies
├── env.template                 # Environment config template
│
├── 📖 Documentation
│   ├── README.md               # This file
│   ├── QUICKSTART.md           # 3-step quick start
│   └── SAFETY_IMPROVEMENTS.md  # ⭐ Medical safety features details
│
├── data/
│   └── traning.json            # Medical product data (7 products)
│
├── rag_system/
│   ├── vector_store.py         # ChromaDB integration + score filtering
│   ├── rag_chain.py            # RAG chain with safety layers
│   ├── retrieval_chain.py      # Backward compatibility
│   └── utils/
│       └── common.py           # Helper functions
│
├── data_loader.py              # JSON loader with medical fields parsing
└── chroma_db/                  # Vector database (auto-created)
```

## 💡 Usage Examples

### ✅ Valid Questions (Answered with Sources)
```
👤 User: The Fucoidan là gì?
🤖 Bot: The Fucoidan là sản phẩm chứa 100% tinh chất Fucoidan 
        chiết xuất từ Tảo nâu Okinawa Mozuku Nhật Bản...
        
        📚 Nguồn thông tin:
          1. The Fucoidan
        
        ⚠️ Lưu ý: Thông tin chỉ mang tính tham khảo...

👤 User: Giá bao nhiêu?
🤖 Bot: The Fucoidan có giá 2.200.000₫ cho hộp 90 viên.
        
        📚 Nguồn thông tin:
          1. The Fucoidan

👤 User: Liều dùng như thế nào?
🤖 Bot: Liều dùng The Fucoidan:
        - Duy trì: 3 viên/ngày
        - Tăng cường: 6 viên/ngày (2 lần/ngày, mỗi lần 3 viên)
        
        📚 Nguồn thông tin:
          1. The Fucoidan
```

### 🚫 Blocked Questions (Safety Protection)
```
👤 User: Tôi bị đau bụng nên uống thuốc gì?
🤖 Bot: ⚠️ TÔI KHÔNG THỂ ĐƯA RA CHỈ ĐỊNH Y TẾ
        
        Câu hỏi của bạn liên quan đến chẩn đoán hoặc chỉ định điều trị.
        Đây là việc chỉ bác sĩ hoặc dược sĩ mới có thể làm.
        
        🏥 Vui lòng:
        - Tham khảo ý kiến bác sĩ
        - Đến nhà thuốc gặp dược sĩ

👤 User: Aspirin có tác dụng gì? (not in database)
🤖 Bot: ❌ Tôi không tìm thấy thông tin phù hợp trong cơ sở dữ liệu
        để trả lời câu hỏi này.
        
        💡 Vui lòng:
        - Thử diễn đạt câu hỏi khác đi
        - Liên hệ dược sĩ hoặc tra cứu tài liệu chính thức
```

## 📝 Adding New Data

1. **Edit data file:**

```json
// data/traning.json
[
  {
    "name": "Product Name",
    "metadata": "Detailed product information..."
  }
]
```

2. **Delete existing database:**

```bash
rm -rf chroma_db/
```

3. **Restart the app:**

```bash
streamlit run app.py
```

The app will auto-reinitialize with the new data!

## 🔧 Configuration

### Adjust Chunking

**File:** `data_loader.py`

```python
load_and_chunk_json(
    json_file,
    chunk_size=1000,      # Chunk size in characters
    chunk_overlap=200      # Overlap between chunks
)
```

### Adjust Retrieval

**File:** `rag_system/rag_chain.py`

```python
self.retriever = self.vector_store.get_retriever(
    k=5,                  # Number of documents to retrieve
    score_threshold=None  # Similarity threshold (0-1)
)
```

### Adjust LLM

**File:** `rag_system/rag_chain.py`

```python
ChatGroq(
    model="llama-3.3-70b-versatile",  # Model name
    temperature=0.7,                   # Creativity (0-1)
    max_tokens=8000                    # Max response length
)
```

### Adjust Memory

**File:** `rag_system/rag_chain.py`

```python
ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    k=5  # Keep last 5 conversation exchanges
)
```

## 🆚 Why ChromaDB?

| Feature | ChromaDB | Pinecone |
|---------|----------|----------|
| **Cost** | 100% Free | Free tier limited |
| **Location** | Local | Cloud |
| **API Key** | Not needed | Required |
| **Speed** | Fast (local) | Fast (optimized) |
| **Privacy** | High (local) | Cloud-dependent |
| **Setup** | Simple | Need API key |
| **Scale** | Small-medium | Large scale |

**Use ChromaDB for:**
- ✅ Development & prototyping
- ✅ Sensitive data (medical, financial)
- ✅ Budget constraints
- ✅ Data < 1M vectors

## 🐛 Troubleshooting

### Error: "GROQ_API_KEY not found"

**Solution:**
```bash
# Check if .env exists
cat .env

# If not, create it
cp env.template .env
# Then edit .env and add your API key
```

### Error: "Cannot download model"

**Cause:** Internet connection or HuggingFace access issue

**Solution:**
1. Check internet connection
2. If in Vietnam, may need VPN for first download
3. After download completes, can run offline

### ChromaDB not initializing

**Solution:**
```bash
# Delete existing database
rm -rf chroma_db/

# Restart app (will auto-reinitialize)
streamlit run app.py
```

### Chatbot gives incorrect answers

**Check:**
1. Is `data/traning.json` complete?
2. Try increasing retrieval count: `k=10` in `get_retriever()`
3. Delete and reinitialize ChromaDB

## 🔑 Free API Keys

### Groq AI (Recommended)
- **Website:** https://console.groq.com/keys
- **Free Tier:** 14,400 requests/day, 30/minute
- **Speed:** <500ms response time
- **Model:** Llama 3.3 70B (70 billion parameters!)

## 📚 Tech Stack

- **LangChain** - RAG framework
- **ChromaDB** - Vector database
- **Groq AI** - LLM inference
- **HuggingFace** - Multilingual embeddings
- **Streamlit** - Web UI

## 📖 Documentation

- [LangChain Docs](https://python.langchain.com/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Groq AI Docs](https://console.groq.com/docs)
- [Streamlit Docs](https://docs.streamlit.io/)

## 🎯 Medical Products Included

The chatbot provides information about:

1. **The Fucoidan** - Cancer support (Okinawa Mozuku seaweed)
2. **The Fucoidan xK** - Enhanced version (3-in-1 formula)
3. **β-Glucan Ball** - 9 Japanese mushroom extract
4. **Kidney & Men's** - Male health support
5. **Power HLP** - Stroke prevention (earthworm extract)
6. **The Reishi** - Reishi mushroom + Agaricus
7. **Paracetamol** - Pain relief and fever reduction

## ⚡ Performance

- **First Run:** 3-5 minutes (downloads model + creates database)
- **Subsequent Runs:** <10 seconds (loads from disk)
- **Response Time:** <2 seconds per query
- **Memory Usage:** ~2GB RAM

## 📚 Documentation

- [VIETNAMESE_NORMALIZATION.md](VIETNAMESE_NORMALIZATION.md) - Vietnamese text normalization (no diacritics → proper Vietnamese)
- [CONDITION_DETECTION.md](CONDITION_DETECTION.md) - Intelligent medical condition detection
- [CONTEXT_FIX.md](CONTEXT_FIX.md) - Chat history context preservation
- [SAFETY_IMPROVEMENTS.md](SAFETY_IMPROVEMENTS.md) - Medical safety features
- [TESTING.md](TESTING.md) - Testing guide
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide

## 🤝 Contributing

Contributions welcome! Feel free to:
1. Add more medical products to `data/traning.json`
2. Improve prompt engineering
3. Enhance UI/UX
4. Add more features

## 📄 License

MIT License - Free to use for your projects!

## 👨‍💻 Author

AI Master Hackathon Team

---

**🎉 Happy Chatting!**

Need help? Check the troubleshooting section above or open an issue.
