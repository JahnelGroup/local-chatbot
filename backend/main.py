from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from rag import RAGEngine
from embed import EmbeddingService
from vector_store import VectorStoreService
import shutil
import tempfile
from typing import List, Dict, Any, Union

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Local Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
embedding_service = EmbeddingService()
vector_store = VectorStoreService()
rag_engine = RAGEngine(embedding_service, vector_store)

class ChatRequest(BaseModel):
    query: str

class Citation(BaseModel):
    source: str
    page: Union[int, str]  # Allow both int and string for page numbers
    excerpt: str
    relevance_score: float
    chunk_id: int

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    citations: List[Citation] = []

@app.get("/")
async def root():
    return {"message": "Local Chatbot API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that handles user queries using RAG with detailed citations
    """
    try:
        response, sources, citations = await rag_engine.query(request.query)
        
        # Convert citation dictionaries to Citation models
        citation_models = [Citation(**citation) for citation in citations]
        
        return ChatResponse(
            response=response, 
            sources=sources, 
            citations=citation_models
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload PDF file endpoint
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # Store the file info for ingestion
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        final_path = os.path.join(uploads_dir, file.filename)
        shutil.move(tmp_path, final_path)
        
        return {"message": f"File {file.filename} uploaded successfully", "file_path": final_path}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/ingest")
async def ingest_documents():
    """
    Ingest all uploaded PDFs into the vector store
    """
    try:
        uploads_dir = "uploads"
        if not os.path.exists(uploads_dir):
            raise HTTPException(status_code=404, detail="No uploads directory found")
        
        pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            raise HTTPException(status_code=404, detail="No PDF files found to ingest")
        
        ingested_files = []
        for pdf_file in pdf_files:
            file_path = os.path.join(uploads_dir, pdf_file)
            await rag_engine.ingest_document(file_path)
            ingested_files.append(pdf_file)
        
        return {"message": f"Successfully ingested {len(ingested_files)} documents", "files": ingested_files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting documents: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "ollama_available": embedding_service.check_ollama_connection()}

@app.get("/debug/stats")
async def debug_stats():
    """Debug endpoint to check vector store contents"""
    try:
        stats = rag_engine.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/debug/test-query")
async def debug_test_query():
    """Debug endpoint to test the enhanced citation system"""
    try:
        test_query = "What is this about?"
        response, sources, citations = await rag_engine.query(test_query, k=3)
        
        return {
            "query": test_query,
            "response": response,
            "sources": sources,
            "citations": citations,
            "citation_count": len(citations)
        }
    except Exception as e:
        logger.error(f"Error in debug test query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in test query: {str(e)}")

@app.get("/uploads")
async def list_uploads():
    """Get list of uploaded files"""
    try:
        uploads_dir = Path("uploads")
        if not uploads_dir.exists():
            return {"files": []}
        
        files = []
        for file_path in uploads_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })
        
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing uploads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document and all its embeddings"""
    try:
        result = await rag_engine.delete_document(filename)
        return result
    except Exception as e:
        logger.error(f"Error deleting document {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 