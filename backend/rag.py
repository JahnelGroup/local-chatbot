import os
import requests
from typing import List, Tuple, Dict, Any
import PyPDF2
import re
from embed import EmbeddingService
from vector_store import VectorStoreService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStoreService):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.llm_model = os.getenv("LLM_MODEL", "mistral")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

    def extract_text_from_pdf_with_pages(self, pdf_path: str) -> List[Tuple[str, int]]:
        """Extract text from PDF file with page numbers"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pages_text = []
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():  # Only include pages with text
                        pages_text.append((text, page_num))
                return pages_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file (legacy method for compatibility)"""
        pages_text = self.extract_text_from_pdf_with_pages(pdf_path)
        return "\n".join([text for text, _ in pages_text])

    def chunk_text_with_page_info(self, pages_text: List[Tuple[str, int]], chunk_size: int = None, chunk_overlap: int = None) -> List[Tuple[str, int, int, int]]:
        """
        Split text into overlapping chunks while preserving page information
        Returns: List of (chunk_text, page_number, char_start, char_end)
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        if chunk_overlap is None:
            chunk_overlap = self.chunk_overlap
        
        chunks = []
        overall_position = 0
        
        for page_text, page_num in pages_text:
            # Clean the text
            cleaned_text = re.sub(r'\s+', ' ', page_text.strip())
            page_start_position = overall_position
            
            # Create chunks for this page
            start = 0
            while start < len(cleaned_text):
                end = start + chunk_size
                
                # Try to break at sentence or word boundary
                if end < len(cleaned_text):
                    sentence_end = cleaned_text.rfind('.', start, end)
                    if sentence_end != -1 and sentence_end > start + chunk_size // 2:
                        end = sentence_end + 1
                    else:
                        word_end = cleaned_text.rfind(' ', start, end)
                        if word_end != -1 and word_end > start + chunk_size // 2:
                            end = word_end
                
                chunk_text = cleaned_text[start:end].strip()
                if chunk_text:
                    char_start = page_start_position + start
                    char_end = page_start_position + end
                    chunks.append((chunk_text, page_num, char_start, char_end))
                
                start = end - chunk_overlap
                if start >= len(cleaned_text):
                    break
            
            overall_position += len(cleaned_text) + 1  # +1 for page separator
        
        return chunks

    def chunk_text(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
        """Split text into overlapping chunks (legacy method for compatibility)"""
        if chunk_size is None:
            chunk_size = self.chunk_size
        if chunk_overlap is None:
            chunk_overlap = self.chunk_overlap
        
        # Clean the text
        text = re.sub(r'\s+', ' ', text.strip())
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If we're not at the end, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                sentence_end = text.rfind('.', start, end)
                if sentence_end != -1 and sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end != -1 and word_end > start + chunk_size // 2:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - chunk_overlap
            if start >= len(text):
                break
        
        return chunks

    async def ingest_document(self, pdf_path: str) -> None:
        """Ingest a PDF document into the vector store with enhanced metadata"""
        try:
            logger.info(f"Ingesting document: {pdf_path}")
            
            # Extract text from PDF with page numbers
            pages_text = self.extract_text_from_pdf_with_pages(pdf_path)
            
            # Split into chunks with page information
            chunk_data = self.chunk_text_with_page_info(pages_text)
            logger.info(f"Created {len(chunk_data)} chunks from {pdf_path}")
            
            # Extract just the text for embeddings
            chunks = [chunk_text for chunk_text, _, _, _ in chunk_data]
            
            # Generate embeddings
            embeddings = self.embedding_service.embed_documents(chunks)
            
            # Create enhanced metadata
            filename = os.path.basename(pdf_path)
            metadatas = []
            for i, (chunk_text, page_num, char_start, char_end) in enumerate(chunk_data):
                # Create a preview of the chunk (first 100 characters)
                preview = chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text
                
                metadatas.append({
                    "source": filename,
                    "chunk_id": i,
                    "chunk_length": len(chunk_text),
                    "page_number": page_num,
                    "char_start": char_start,
                    "char_end": char_end,
                    "preview": preview
                })
            
            # Add to vector store
            self.vector_store.add_documents(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully ingested {filename}")
            
        except Exception as e:
            logger.error(f"Error ingesting document {pdf_path}: {e}")
            raise

    def retrieve_relevant_chunks(self, query: str, k: int = 5) -> List[Tuple[str, Dict[str, Any], float]]:
        """Retrieve relevant document chunks for a query"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_query(query)
            logger.info(f"Generated query embedding for: '{query[:50]}...'")
            
            # Search vector store
            results = self.vector_store.similarity_search(
                query_embedding=query_embedding,
                k=k,
                score_threshold=None  # No threshold - return top k results
            )
            
            logger.info(f"Found {len(results)} relevant chunks with scores: {[f'{score:.3f}' for _, _, score in results]}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []

    def build_context_prompt(self, query: str, context_chunks: List[Tuple[str, Dict[str, Any], float]]) -> Tuple[str, List[str], List[Dict[str, Any]]]:
        """Build the context-augmented prompt and return citation information"""
        context_text = ""
        sources = []
        citations = []
        
        for i, (chunk, metadata, score) in enumerate(context_chunks):
            source_name = metadata.get('source', 'unknown')
            page_num = metadata.get('page_number', 'N/A')  # Handle missing page numbers gracefully
            
            # Add numbered reference for the context
            if page_num != 'N/A':
                context_text += f"[{i+1}] From {source_name}, page {page_num}:\n{chunk}\n\n"
            else:
                context_text += f"[{i+1}] From {source_name}:\n{chunk}\n\n"
            
            # Track unique sources
            if source_name not in sources:
                sources.append(source_name)
            
            # Create citation object with excerpt - handle missing fields gracefully
            citation = {
                "source": source_name,
                "page": page_num if page_num != 'N/A' else 1,  # Default to page 1 for old documents
                "excerpt": chunk,
                "relevance_score": round(score, 3),
                "chunk_id": metadata.get('chunk_id', i)
            }
            citations.append(citation)
        
        prompt = f"""[CONTEXT BLOCK]

You are a helpful assistant that answers questions based on the provided context. When you reference information, use the reference numbers [1], [2], etc. that correspond to the sources in the context.

Context:
{context_text}

Question:
{query}

Answer (reference your sources using [1], [2], etc.):"""
        
        return prompt, sources, citations

    async def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again later."

    async def query(self, user_query: str, k: int = 5) -> Tuple[str, List[str], List[Dict[str, Any]]]:
        """
        Main query method that implements the RAG pipeline
        Returns: (response, sources, citations)
        """
        try:
            # Step 1: Retrieve relevant chunks
            relevant_chunks = self.retrieve_relevant_chunks(user_query, k=k)
            
            if not relevant_chunks:
                return "I don't have any relevant information to answer your question. Please make sure you've uploaded and ingested some PDF documents first.", [], []
            
            # Step 2: Build context prompt and get citations
            prompt, sources, citations = self.build_context_prompt(user_query, relevant_chunks)
            
            # Step 3: Generate response
            response = await self.generate_response(prompt)
            
            return response, sources, citations
            
        except Exception as e:
            logger.error(f"Error in query pipeline: {e}")
            return f"An error occurred while processing your query: {str(e)}", [], []

    async def delete_document(self, filename: str) -> Dict[str, Any]:
        """Delete a document and all its embeddings from the system"""
        try:
            logger.info(f"Deleting document: {filename}")
            
            # Delete from vector store
            deleted_count = self.vector_store.delete_documents_by_source(filename)
            
            # Delete physical file
            uploads_dir = "uploads"
            file_path = os.path.join(uploads_dir, filename)
            file_deleted = False
            
            if os.path.exists(file_path):
                os.remove(file_path)
                file_deleted = True
                logger.info(f"Deleted physical file: {file_path}")
            else:
                logger.warning(f"Physical file not found: {file_path}")
            
            return {
                "filename": filename,
                "chunks_deleted": deleted_count,
                "file_deleted": file_deleted,
                "message": f"Successfully deleted {filename} and {deleted_count} associated chunks"
            }
            
        except Exception as e:
            logger.error(f"Error deleting document {filename}: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system"""
        return {
            "document_count": self.vector_store.get_document_count(),
            "collection_info": self.vector_store.get_collection_info(),
            "ollama_available": self.embedding_service.check_ollama_connection(),
            "llm_model": self.llm_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        } 