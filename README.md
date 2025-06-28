# Local Chatbot - Offline PDF RAG Application

A local, offline chatbot application for querying PDF content using Retrieval-Augmented Generation (RAG) with Ollama.

## 🚀 Features

- **Local & Offline**: Complete privacy - no data leaves your machine
- **PDF Processing**: Upload and process PDF documents
- **RAG Pipeline**: Advanced retrieval-augmented generation
- **Vector Search**: Semantic search using ChromaDB
- **Modern UI**: Clean React + Tailwind interface
- **Flexible Models**: Support for various Ollama models

## 🏗️ Architecture

```
chatbot-app/
├── backend/          # FastAPI Python backend
│   ├── main.py      # API endpoints
│   ├── rag.py       # RAG pipeline
│   ├── embed.py     # Embedding service
│   └── vector_store.py  # Vector database
├── frontend/        # React + Tailwind UI
│   ├── src/components/  # Reusable components
│   └── src/pages/       # Application pages
└── docker-compose.yml   # Development setup
```

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Ollama** installed and running

### Install Ollama

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull mistral
ollama pull nomic-embed-text
```

## 🛠️ Setup Instructions

### 1. Clone and Setup Backend

```bash
# Navigate to backend
cd chatbot-app/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Frontend

```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install
```

### 3. Start Ollama

```bash
# Start Ollama service
ollama serve

# In another terminal, ensure models are available
ollama list
```

## 🚀 Running the Application

### Start Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend (Terminal 2)

```bash
cd frontend
npm start
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 Usage Guide

### 1. Upload Documents
1. Navigate to the "Upload" tab
2. Drag & drop PDF files or click to select
3. Click "Process Documents" to ingest into vector database

### 2. Chat with Documents
1. Navigate to the "Chat" tab
2. Ask questions about your uploaded documents
3. The system will provide answers with source references

## 🔧 Configuration

### Environment Variables

Edit `.env` file to customize:

```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
LLM_MODEL=mistral
EMBEDDING_MODEL=nomic-embed-text

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# API Configuration
REACT_APP_API_URL=http://localhost:8000
```

### Available Models

You can use any Ollama model:
- `mistral` (recommended)
- `llama3`
- `codellama`
- `neural-chat`

## 🐳 Docker Development (Optional)

```bash
# Start everything with Docker
docker-compose up --build

# Access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send chat query |
| `/upload` | POST | Upload PDF file |
| `/ingest` | POST | Process uploaded files |
| `/health` | GET | Health check |

## 🔍 How It Works

1. **Document Upload**: PDFs are uploaded and stored locally
2. **Text Extraction**: PyPDF2 extracts text from documents
3. **Chunking**: Text is split into overlapping chunks
4. **Embedding**: Chunks are embedded using Ollama/SentenceTransformers
5. **Vector Storage**: Embeddings stored in ChromaDB
6. **Query Processing**: User queries are embedded and searched
7. **Response Generation**: Relevant chunks sent to LLM for response

## 🛠️ Troubleshooting

### Common Issues

**Ollama Connection Error**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama if not running
ollama serve
```

**Model Not Found**
```bash
# Pull required models
ollama pull mistral
ollama pull nomic-embed-text
```

**Port Already in Use**
```bash
# Change ports in .env file
REACT_APP_API_URL=http://localhost:8001

# Start backend on different port
uvicorn main:app --port 8001
```

### Performance Tips

- **RAM**: Ensure sufficient RAM for embeddings (4GB+ recommended)
- **Storage**: Vector database grows with document count
- **Models**: Smaller models run faster but may be less accurate

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama** for local LLM inference
- **ChromaDB** for vector storage
- **FastAPI** for the backend framework
- **React + Tailwind** for the frontend 