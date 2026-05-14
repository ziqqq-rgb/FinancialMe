import os
import pickle
import logging
import re  # ADDED: Regular expressions for robust text processing
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridIndexer:
    
    def __init__(self, chroma_persist_dir: str = "../data/chromadb_store", bm25_persist_path: str = "../data/bm25_index.pkl"):
        self.chroma_persist_dir = chroma_persist_dir
        self.bm25_persist_path = bm25_persist_path
        
        os.makedirs(os.path.dirname(self.chroma_persist_dir), exist_ok=True)
        
        logger.info("Initializing Embedding Model (BAAI/bge-m3)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    def _tokenize_text(self, text: str) -> List[str]:
       
        # Lowercase the text to ensure case-insensitive matching
        lowercased = text.lower()
        
        # Find all alphanumeric sequences (matches words like "revenue" and numbers like "2026")
        # Automatically drops raw punctuation tokens like $, %, (), or commas
        tokens = re.findall(r'\b\w+\b', lowercased)
        
        # Filter out very short noise tokens (e.g., "a", "i", "x") but keep important numbers
        return [token for token in tokens if len(token) > 1 or token.isdigit()]

    def index_documents(self, documents: List[Document]):
        
        if not documents:
            logger.warning("No documents provided for indexing.")
            return
            
        logger.info(f"Starting hybrid indexing for {len(documents)} chunks...")

        logger.info("1/2: Embedding documents and storing in ChromaDB...")
        try:
            vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.chroma_persist_dir,
                collection_name="financial_reports"
            )
            logger.info(f"Successfully persisted vectors to {self.chroma_persist_dir}")
        except Exception as e:
            logger.error(f"Failed to index into ChromaDB: {str(e)}")
            raise e

        # --- 2. Sparse Indexing (BM25) ---
        logger.info("2/2: Building BM25 sparse keyword index...")
        try:
            # CHANGED: Utilizing the new robust tokenization method
            tokenized_corpus = [self._tokenize_text(doc.page_content) for doc in documents]
            bm25_index = BM25Okapi(tokenized_corpus)
            
            # We must save the documents alongside the BM25 index so we can retrieve them later
            bm25_data = {
                "index": bm25_index,
                "documents": documents
            }
            
            with open(self.bm25_persist_path, "wb") as f:
                pickle.dump(bm25_data, f)
            logger.info(f"Successfully saved BM25 index to {self.bm25_persist_path}")
        except Exception as e:
            logger.error(f"Failed to build/save BM25 index: {str(e)}")
            raise e

        logger.info("=== HYBRID INDEXING COMPLETE ===")



