# 🧠 AI Document Search Intelligence System

> **Production-grade RAG-powered Document Search & Chat Platform**
> Built with FastAPI · LangChain · FAISS · React · Tailwind CSS

---

## 📸 Screenshots

```
┌─────────────────────────────────────────────────────────┐
│  Sidebar (Document KB)  │     Chat Interface             │
│  ─────────────────────  │  ───────────────────────────   │
│  📄 report.pdf  ✅      │  User: What are the KPIs?      │
│  📄 manual.docx ✅      │                                │
│  📄 notes.txt   🔄      │  AI: Based on the documents,   │
│                         │  the KPIs include...           │
│  [Chat] [Upload]        │  [Source: report.pdf, p.3] ↗  │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Status |
|---|---|
| PDF / DOCX / TXT / MD upload | ✅ |
| Intelligent token-aware chunking | ✅ |
| FAISS vector store (local, persistent) | ✅ |
| HuggingFace embeddings (no API key needed) | ✅ |
| OpenAI GPT-4o / gpt-4o-mini support | ✅ |
| Ollama local LLM support | ✅ |
| Streaming responses (SSE) | ✅ |
| Source citations with page numbers | ✅ |
| Session-based chat memory | ✅ |
| Multi-document filtering | ✅ |
| Document summarization | ✅ |
| Anti-hallucination guardrails | ✅ |
| Background indexing | ✅ |
| Docker Compose deployment | ✅ |
| ChromaDB support (optional) | ✅ |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (React)                        │
│   Upload UI  ──→  REST POST /upload                         │
│   Chat UI    ──→  SSE  POST /chat  (streaming tokens)       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                              │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐  │
│  │  Upload API  │   │   Chat API   │   │  Documents API   │  │
│  └──────┬──────┘   └──────┬───────┘   └──────────────────┘  │
│         │                 │                                   │
│  ┌──────▼─────────────────▼───────────────────────────────┐  │
│  │                  RAG Pipeline                           │  │
│  │                                                         │  │
│  │  Document Loader → Text Splitter → Embeddings          │  │
│  │         ↓                                ↓             │  │
│  │  [PDF/DOCX/TXT]   [1000 char chunks]  [MiniLM/OpenAI] │  │
│  │                                           ↓             │  │
│  │  Query → Embed → FAISS Search → Context → LLM → Answer│  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────┐   ┌────────────────────────────────┐   │
│  │  FAISS / Chroma │   │  JSON Store (→ PostgreSQL)     │   │
│  │  Vector Index   │   │  Documents · Sessions          │   │
│  └─────────────────┘   └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Clone
```bash
git clone https://github.com/Ashish-Prasad-525/Summer-Internship.git
cd ai-document-rag-system
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set OPENAI_API_KEY if using OpenAI LLM/embeddings
# Default config uses HuggingFace embeddings (no key needed) + requires OpenAI for LLM

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd frontend

npm install

# Optional: create .env.local
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env.local

npm run dev
# → http://localhost:3000
```

### 4. Open the app
Navigate to **http://localhost:3000**

1. Click **Upload Documents** → drag in a PDF or DOCX
2. Wait for "indexed" status (green dot, ~5–30s)
3. Click **Chat with Documents** → ask questions!

---

## 🐳 Docker Deployment

```bash
# Copy and fill in your environment file
cp backend/.env.example backend/.env
# Set at minimum: OPENAI_API_KEY (if using OpenAI)

# Build and start all services
docker compose up --build

# Backend:  http://localhost:8000
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/api/docs
```

Data is persisted in `./data/` and `./vectorstore/` on the host.

---

## ☁️ Cloud Deployment

### Render.com (recommended free tier)
1. Push repo to GitHub
2. New Web Service → connect repo
3. **Backend**: Root = `backend/`, Build = `pip install -r requirements.txt`, Start = `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add all `.env` values as Environment Variables
5. **Frontend**: New Static Site → Root = `frontend/`, Build = `npm install && npm run build`, Publish = `dist/`
6. Set `VITE_API_URL` to your Render backend URL

### Railway
```bash
# Install Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

### Vercel (Frontend only)
```bash
cd frontend
npx vercel --prod
# Set VITE_API_URL to your backend URL in Vercel dashboard
```

---

## ⚙️ Configuration Reference

All settings live in `backend/.env`. Key options:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` or `ollama` |
| `OPENAI_API_KEY` | — | Required for OpenAI LLM |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model name |
| `EMBEDDING_PROVIDER` | `huggingface` | `huggingface` or `openai` |
| `HF_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local embedding model |
| `VECTOR_STORE_TYPE` | `faiss` | `faiss` or `chroma` |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RETRIEVAL` | `5` | Chunks retrieved per query |
| `SIMILARITY_THRESHOLD` | `0.3` | Min relevance score (0–1) |
| `MAX_FILE_SIZE_MB` | `50` | Upload size limit |

### Using Ollama (free local LLM)
```bash
# Install Ollama: https://ollama.ai
ollama pull llama3

# In .env:
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 📡 API Reference

### Upload
```http
POST /api/v1/upload/
Content-Type: multipart/form-data

file: <binary>

→ { document_id, filename, status, message }
```

```http
GET /api/v1/upload/status/{document_id}
→ { doc_id, filename, status, chunks_created, ... }
```

### Chat
```http
POST /api/v1/chat/
Content-Type: application/json

{
  "question": "What are the key findings?",
  "session_id": "optional-uuid",
  "document_ids": ["optional-filter-by-doc"],
  "stream": true,
  "top_k": 5
}

# Streaming response (SSE):
# data: {"type":"metadata","session_id":"...","sources":[...]}
# data: {"type":"token","content":"The "}
# data: {"type":"token","content":"key "}
# ...
# data: {"type":"done","full_answer":"..."}
```

```http
POST /api/v1/chat/summarize
{ "document_id": "uuid", "style": "concise|detailed|bullet_points" }
```

### Documents
```http
GET    /api/v1/documents/            # List all documents
DELETE /api/v1/documents/{id}        # Delete document + vectors
GET    /api/v1/documents/stats/overview  # System stats
GET    /api/v1/documents/{id}/chunks # Inspect chunks (debugging)
```

---

## 🧪 Testing

```bash
cd backend

# Install test deps
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Test just the RAG pipeline
pytest tests/test_rag.py -v

# Test API endpoints
pytest tests/test_api.py -v
```

Example test file `backend/tests/test_api.py`:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_list_documents():
    r = client.get("/api/v1/documents/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

---

## 🛠️ Tech Stack

### Backend
| Tool | Role |
|---|---|
| **FastAPI** | Async REST API + SSE streaming |
| **LangChain** | RAG pipeline orchestration |
| **FAISS** | Vector similarity search |
| **pdfplumber** | PDF text extraction |
| **python-docx** | DOCX parsing |
| **SentenceTransformers** | Local embeddings (no API key) |
| **Pydantic** | Data validation & settings |
| **uvicorn** | ASGI server |

### Frontend
| Tool | Role |
|---|---|
| **React 18** | UI framework |
| **TypeScript** | Type safety |
| **Vite** | Build tool |
| **Tailwind CSS** | Styling |
| **react-dropzone** | File upload UI |
| **react-markdown** | Render LLM markdown |
| **Axios + Fetch** | REST + SSE API calls |

---

## 📁 Project Structure

```
ai-document-rag-system/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan, CORS
│   │   ├── config.py            # Pydantic settings (all env vars)
│   │   ├── api/
│   │   │   ├── routes.py        # Router aggregator
│   │   │   ├── upload.py        # POST /upload — file ingestion
│   │   │   ├── chat.py          # POST /chat  — streaming Q&A
│   │   │   └── documents.py     # GET/DELETE /documents
│   │   ├── core/
│   │   │   ├── rag_pipeline.py  # ⭐ RAG orchestration
│   │   │   ├── embeddings.py    # OpenAI / HuggingFace embeddings
│   │   │   ├── vectorstore.py   # FAISS / ChromaDB wrapper
│   │   │   └── document_loader.py  # PDF / DOCX / TXT parsing
│   │   ├── services/
│   │   │   ├── document_service.py  # Metadata CRUD
│   │   │   └── session_service.py   # Chat history
│   │   └── utils/
│   │       ├── file_utils.py    # Hashing, validation
│   │       └── logger.py        # Structured logging
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root layout + state wiring
│   │   ├── main.tsx             # Entry point
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── Sidebar.tsx  # Nav + document KB list
│   │   │   ├── chat/
│   │   │   │   └── ChatPanel.tsx  # Chat UI + source cards
│   │   │   └── upload/
│   │   │       └── UploadPanel.tsx  # Drag & drop upload
│   │   ├── hooks/
│   │   │   ├── useChat.ts       # Chat state + SSE streaming
│   │   │   └── useDocuments.ts  # Document list + polling
│   │   ├── services/
│   │   │   └── api.ts           # Typed axios + SSE client
│   │   └── styles/
│   │       └── globals.css      # Tailwind + custom classes
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── vectorstore/                 # FAISS index (auto-created)
├── data/
│   ├── uploads/                 # Raw uploaded files
│   ├── documents.json           # Document metadata store
│   └── sessions.json            # Chat session store
├── logs/
├── docker-compose.yml
└── README.md
```

---

## 🔒 Security Notes

- Never commit your `.env` file (it's in `.gitignore`)
- Change `SECRET_KEY` and `JWT_SECRET` before deploying
- For production, replace SQLite with PostgreSQL
- Enable rate limiting via `slowapi` (already in requirements)
- Add authentication by implementing the JWT middleware in `app/api/auth.py`

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit: `git commit -m "feat: add my feature"`
4. Push and open a PR

---

## 📄 License

MIT — free to use, modify, and distribute.
