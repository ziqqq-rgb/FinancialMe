import pickle
import logging
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridRetriever:
    
    def __init__(self, chroma_persist_dir: str = "../data/chromadb_store", bm25_persist_path: str = "../data/bm25_index.pkl"):
        logger.info("Initializing Native Hybrid Retriever Pipeline...")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.vector_store = Chroma(
            persist_directory=chroma_persist_dir,
            embedding_function=self.embeddings,
            collection_name="financial_reports"
        )
        
        # Configure vector store to return top 5 results
        vector_retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        # 2. Initialize BM25 Retriever (Sparse)
        try:
            with open(bm25_persist_path, "rb") as f:
                bm25_data = pickle.load(f)
                
            documents = bm25_data["documents"]
            bm25_retriever = BM25Retriever.from_documents(documents)
            bm25_retriever.k = 5
            
        except FileNotFoundError:
            logger.error(f"BM25 index data not found at {bm25_persist_path}. Did you execute the indexer first?")
            raise
            
        # 3. Initialize Native Ensemble Retriever
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever], 
            weights=[0.5, 0.5]
        )

        logger.info("Ensemble Retriever loaded successfully. Ready for queries.")

    def retrieve(self, query: str) -> List[Document]:
        """
        Executes the fused retrieval using LangChain's built-in RRF implementation.
        """
        logger.info(f"Executing ensemble search for query: '{query}'")
        
        final_docs = self.ensemble_retriever.invoke(query)
        logger.info(f"Successfully retrieved and fused {len(final_docs)} documents.")
        return final_docs

# --- Integration Test ---
if __name__ == "__main__":
    
    retriever = HybridRetriever(
        chroma_persist_dir="../data/chromadb_store",
        bm25_persist_path="../data/bm25_index.pkl"
    )
    
    test_query = "What is the total revenue and are there any charts showing this?"
    results = retriever.retrieve(query=test_query)
    
    print("\n=== NATIVE ENSEMBLE HYBRID SEARCH RESULTS ===")
    for i, doc in enumerate(results[:3]):
        print(f"\nRank: {i+1}")
        print(f"Chunk ID: {doc.metadata.get('chunk_id', 'N/A')}")
        print(f"Content Snippet: {doc.page_content[:200]}...\n")
        print("-" * 50)
