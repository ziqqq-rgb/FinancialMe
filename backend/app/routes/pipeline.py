import json
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, QueryResponse, Citation
from retriever.retriever import HybridRetriever
from generation.synthesizer import AnswerSynthesizer

logger = logging.getLogger(__name__)
router = APIRouter()

try:
    retriever = HybridRetriever(
        chroma_persist_dir="test/data/test_chromadb_store", 
        bm25_persist_path="test/data/test_bm25_index.pkl"
    )
    synthesizer = AnswerSynthesizer()
except Exception as e:
    logger.error(f"Failed to initialize AI components: {e}")

@router.post("/query", response_model=QueryResponse)
async def query_pipeline(request: QueryRequest):
    try:
        logger.info(f"Received API query: {request.query}")
        
        # 1. Retrieve the relevant chunks
        docs = retriever.retrieve(query=request.query)
        
        # 2. Generate the text answer
        answer = synthesizer.generate_answer(query=request.query, retrieved_docs=docs)
        
        # 3. Extract the images and text to send back as citations for the UI
        citations = []
        for doc in docs:
            content_dict = json.loads(doc.metadata.get("original_content", "{}"))
            citations.append(
                Citation(
                    chunk_id=str(doc.metadata.get("chunk_id", "unknown")),
                    text=doc.page_content,
                    images_base64=content_dict.get("images_base64", [])
                )
            )
        
        return QueryResponse(answer=answer, citations=citations)
        
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during RAG pipeline execution.")