import os
import uuid
from typing import List, Dict, Any, Tuple
import chromadb
from chromadb.config import Settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self, persist_directory: str = "db", collection_name: str = "documents"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Ensure the directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except ValueError:
            self.collection = self.client.create_collection(name=collection_name)
            logger.info(f"Created new collection: {collection_name}")

    def add_documents(
        self, 
        documents: List[str], 
        embeddings: List[List[float]], 
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ) -> List[str]:
        """
        Add documents to the vector store
        """
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in documents]
        
        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise

    def query(
        self, 
        query_embedding: List[float], 
        n_results: int = 5,
        where: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            raise

    def similarity_search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        score_threshold: float = None
    ) -> List[Tuple[str, Dict[str, Any], float]]:
        """
        Perform similarity search and return documents with metadata and scores
        """
        results = self.query(query_embedding, n_results=k)
        
        search_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"], 
            results["metadatas"], 
            results["distances"]
        )):
            # Convert distance to similarity score (lower distance = higher similarity)
            score = 1.0 - distance if distance is not None else 0.0
            
            # Apply score threshold if specified
            if score_threshold is None or score >= score_threshold:
                search_results.append((doc, metadata, score))
        
        return search_results

    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by IDs
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from vector store")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise

    def update_document(
        self, 
        id: str, 
        document: str = None, 
        embedding: List[float] = None, 
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Update a document in the vector store
        """
        try:
            update_dict = {"ids": [id]}
            
            if document is not None:
                update_dict["documents"] = [document]
            if embedding is not None:
                update_dict["embeddings"] = [embedding]
            if metadata is not None:
                update_dict["metadatas"] = [metadata]
            
            self.collection.update(**update_dict)
            logger.info(f"Updated document with id: {id}")
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise

    def get_document_count(self) -> int:
        """
        Get the total number of documents in the collection
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0

    def clear_collection(self) -> None:
        """
        Clear all documents from the collection
        """
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name)
            logger.info("Cleared all documents from collection")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

    def delete_documents_by_source(self, source_filename: str) -> int:
        """
        Delete all documents that match a specific source filename
        Returns the number of documents deleted
        """
        try:
            # First, get all documents with this source to count them
            results = self.collection.get(
                where={"source": source_filename}
            )
            
            if not results["ids"]:
                logger.info(f"No documents found for source: {source_filename}")
                return 0
            
            # Delete the documents
            self.collection.delete(
                where={"source": source_filename}
            )
            
            deleted_count = len(results["ids"])
            logger.info(f"Deleted {deleted_count} documents for source: {source_filename}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting documents by source {source_filename}: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection
        """
        return {
            "name": self.collection_name,
            "document_count": self.get_document_count(),
            "persist_directory": self.persist_directory
        } 