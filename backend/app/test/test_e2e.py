import os
import sys
import logging
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import AnswerRelevancy, Faithfulness

# Add the app directory to the system path so we can import your modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ingestion.parser import document_parser
from ingestion.chunker import DataChunker
from ingestion.summarizer import ContentSummarizer
from ingestion.indexer import HybridIndexer
from retriever.retriever import HybridRetriever
from generation.synthesizer import AnswerSynthesizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_end_to_end_test(pdf_path: str, test_query: str):
    logger.info("=== STARTING E2E RAG PIPELINE TEST ===")

    TEST_CHROMA_DIR = "./data/test_chromadb_store"
    TEST_BM25_PATH = "./data/test_bm25_index.pkl"

    # ==========================================
    # PHASE 1: INGESTION (Upload New File)
    # ==========================================
    logger.info("\n--- PHASE 1: INGESTION ---")
    
    parser = document_parser()
    doc = parser.process_document(pdf_path)
    
    chunker = DataChunker()
    raw_chunks = chunker.process_and_chunk(doc)
    
    summarizer = ContentSummarizer()
    final_chunks = summarizer.process_all_chunks(raw_chunks)
    
    indexer = HybridIndexer(
        chroma_persist_dir=TEST_CHROMA_DIR, 
        bm25_persist_path=TEST_BM25_PATH
    )
    indexer.index_documents(final_chunks)

    # ==========================================
    # PHASE 2: RETRIEVAL
    # ==========================================
    logger.info("\n--- PHASE 2: HYBRID RETRIEVAL ---")
    retriever = HybridRetriever(
        chroma_persist_dir=TEST_CHROMA_DIR, 
        bm25_persist_path=TEST_BM25_PATH
    )
    retrieved_docs = retriever.retrieve(query=test_query)

    # ==========================================
    # PHASE 3: GENERATION
    # ==========================================
    logger.info("\n--- PHASE 3: SYNTHESIS ---")
    synthesizer = AnswerSynthesizer()
    final_answer = synthesizer.generate_answer(query=test_query, retrieved_docs=retrieved_docs)
    
    print("\n" + "="*50)
    print(f"USER QUERY: {test_query}")
    print(f"AI ANSWER:\n{final_answer}")
    print("="*50 + "\n")

    # ==========================================
    # PHASE 4: EVALUATION (Ragas)
    # ==========================================
    logger.info("\n--- PHASE 4: EVALUATION ---")
    
    # Ragas requires contexts to be a list of strings
    contexts_text = [doc.page_content for doc in retrieved_docs]
    
    # Format data for the Ragas Dataset
    eval_data = {
        "question": [test_query],
        "answer": [final_answer],
        "contexts": [contexts_text]
    }
    
    dataset = Dataset.from_dict(eval_data)
    
    # Run Evaluation
    logger.info("Evaluating with Ragas (This takes a few seconds as it calls LLM for grading)...")
    result = evaluate(
        dataset,
        metrics=[
            Faithfulness(),       # Measures if the answer is completely backed by the retrieved context (No Hallucinations)
            AnswerRelevancy()    # Measures if the answer directly addresses the user's question
        ]
    )

    print("\n=== EVALUATION RESULTS ===")
    # Scores are from 0.0 to 1.0 (Higher is better)
    print(f"Faithfulness Score: {result['faithfulness']:.2f}")
    print(f"Answer Relevancy Score: {result['answer_relevancy']:.2f}")
    
    if result['faithfulness'] < 0.8:
        print("WARNING: The AI may have hallucinated information not present in the document.")
    if result['answer_relevancy'] < 0.8:
        print("WARNING: The AI answer might not directly address the user's specific question.")


if __name__ == "__main__":
    # Dynamically get the absolute path to the 'test' directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Point exactly to sample2.pdf inside that test directory
    TEST_PDF = os.path.join(current_dir, "sample2.pdf")    
    TEST_QUESTION = "What were Tesla's Total Automotive Revenues in Q1-2026?"
    
    if not os.path.exists(TEST_PDF):
        logger.error(f"Cannot find test file at {TEST_PDF}")
    else:
        run_end_to_end_test(TEST_PDF, TEST_QUESTION)