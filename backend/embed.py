import os
import requests
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, use_ollama: bool = True, model_name: str = "nomic-embed-text"):
        self.use_ollama = use_ollama
        self.model_name = model_name
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        if not use_ollama:
            logger.info("Loading SentenceTransformer model...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.sentence_model = None
            logger.info(f"Using Ollama embeddings with model: {model_name}")

    def check_ollama_connection(self) -> bool:
        """Check if Ollama is available and responsive"""
        try:
            response = requests.get(f"{self.ollama_url}/api/version", timeout=5)
            return response.status_code == 200
        except:
            return False

    def embed_text_ollama(self, text: str) -> List[float]:
        """Generate embeddings using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result["embedding"]
        except Exception as e:
            logger.error(f"Error generating Ollama embeddings: {e}")
            # Fallback to sentence-transformers
            if self.sentence_model is None:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            return self.sentence_model.encode(text).tolist()

    def embed_text_sentence_transformer(self, text: str) -> List[float]:
        """Generate embeddings using SentenceTransformers"""
        return self.sentence_model.encode(text).tolist()

    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text or list of texts
        """
        if isinstance(text, str):
            if self.use_ollama and self.check_ollama_connection():
                return self.embed_text_ollama(text)
            else:
                if self.sentence_model is None:
                    logger.info("Loading SentenceTransformer model as fallback...")
                    self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                return self.embed_text_sentence_transformer(text)
        
        elif isinstance(text, list):
            embeddings = []
            for t in text:
                embeddings.append(self.embed_text(t))
            return embeddings
        
        else:
            raise ValueError("Text must be string or list of strings")

    def embed_query(self, query: str) -> List[float]:
        """Convenience method for embedding queries"""
        return self.embed_text(query)

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Convenience method for embedding multiple documents"""
        return self.embed_text(documents)

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        if self.use_ollama and self.check_ollama_connection():
            # Test with a short text to get dimension
            test_embedding = self.embed_text_ollama("test")
            return len(test_embedding)
        else:
            if self.sentence_model is None:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            return self.sentence_model.get_sentence_embedding_dimension() 