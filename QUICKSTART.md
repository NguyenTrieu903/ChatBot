# ⚡ Quick Start Guide

## 3 Steps to Run the Chatbot

### Step 1: Install Dependencies
```bash
cd AI_Master_Hackathon
pip install -r requirements.txt
```

### Step 2: Setup API Key
```bash
# Copy template
cp env.template .env

# Edit .env and add your Groq API key
# Get free key at: https://console.groq.com/keys
```

Or create `.env` manually:
```
GROQ_API_KEY=your-api-key-here
```

### Step 3: Run the App
```bash
streamlit run app.py
```

**That's it!** 🎉

The app will:
- ✅ Auto-download embedding model (first time only, ~1.5GB)
- ✅ Auto-initialize ChromaDB vector database
- ✅ Load medical data from `data/traning.json`
- ✅ Open web browser at `http://localhost:8501`

## First Run vs Subsequent Runs

**First Run:** 3-5 minutes (downloads model + creates database)  
**After That:** <10 seconds (everything cached!)

## Troubleshooting

### Missing API Key?
```bash
# Make sure .env file exists
cat .env

# Should see: GROQ_API_KEY=gsk_...
```

### Need to Reset Database?
```bash
# Delete database (will auto-recreate on next run)
rm -rf chroma_db/

# Windows PowerShell:
Remove-Item -Recurse -Force chroma_db
```

## What Happens on First Run?

1. 📥 Downloads `multilingual-e5-large` model (~1.5GB)
2. 📄 Reads `data/traning.json` (7 medical products)
3. ✂️ Chunks documents (chunk_size=1000, overlap=200)
4. 🔢 Creates embeddings (1024-dimensional vectors)
5. 💾 Saves to ChromaDB (local SQLite database)
6. 🚀 Starts Streamlit web UI

## Next Steps

- 📖 Read full documentation: `README.md`
- 🎨 Customize the UI: Edit `app.py`
- 📝 Add more data: Edit `data/traning.json`
- ⚙️ Configure RAG: Edit `rag_system/rag_chain.py`

---

**Need help?** Check `README.md` for detailed documentation!
