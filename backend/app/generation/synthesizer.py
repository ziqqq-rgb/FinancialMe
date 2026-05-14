import json
import logging
import os
from typing import List
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnswerSynthesizer:
    
    def __init__(self):
        logger.info("Initializing Answer Synthesizer with GPT-4o...")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  
            temperature=0.0,
            base_url="https://models.github.ai/inference",
            api_key=api_key
        )
        
        self.system_prompt = SystemMessage(
            content=(
                "You are an expert financial analyst assistant. "
                "You will be provided with a user query and highly relevant context extracted from a corporate document. "
                "This context may include raw text, HTML tables, and images (charts/graphs). "
                "Your job is to synthesize this information to provide a clear, accurate, and direct answer. "
                "If the answer relies on a specific chart or table, explicitly mention it in your response. "
                "If the provided context does not contain the answer, state that clearly. Do not hallucinate."
            )
        )

    def generate_answer(self, query: str, retrieved_docs: List[Document]) -> str:
        
        logger.info(f"Synthesizing answer for query: '{query}' using {len(retrieved_docs)} chunks.")
        
        messages_content = []
        messages_content.append({"type": "text", "text": f"User Query: {query}\n\n--- CONTEXT ---"})

        for i, doc in enumerate(retrieved_docs):
            try:
                content_dict = json.loads(doc.metadata.get("original_content", "{}"))
                
                # 1. Add Text Context
                if content_dict.get("raw_text"):
                    messages_content.append({
                        "type": "text",
                        "text": f"\n[Context Chunk {i+1} Text]:\n{content_dict['raw_text']}"
                    })
                
                # 2. Add Table Context
                for table_html in content_dict.get("tables_html", []):
                    messages_content.append({
                        "type": "text",
                        "text": f"\n[Context Chunk {i+1} Table Data]:\n{table_html}"
                    })
                
                # 3. Add Image Context
                for img_base64 in content_dict.get("images_base64", []):
                    messages_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to parse metadata for chunk {doc.metadata.get('chunk_id')}: {str(e)}")
                # Fallback to standard text payload
                messages_content.append({
                    "type": "text",
                    "text": f"\n[Context Chunk {i+1}]:\n{doc.page_content}"
                })

        # Assemble the clean structural human message payload
        human_message = HumanMessage(content=messages_content)
        
        try:
            logger.info("Calling LLM to generate final response...")
            response = self.llm.invoke([self.system_prompt, human_message])
            logger.info("Generation complete.")
            return response.content
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            raise e

# --- Integration Test ---
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv() 
    
    # Correcting workspace paths dynamically for uniform runtime access
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from retriever.retriever import HybridRetriever

    # 1. Retrieve the data
    
    retriever = HybridRetriever(
        chroma_persist_dir="../data/chromadb_store",
        bm25_persist_path="../data/bm25_index.pkl"
    )
    
    test_query = "What is Multi-Head Attention?"
    retrieved_docs = retriever.retrieve(query=test_query)
    
    # 2. Synthesize the answer
    synthesizer = AnswerSynthesizer()
    final_answer = synthesizer.generate_answer(query=test_query, retrieved_docs=retrieved_docs)
    
    print("\n=== FINAL AI RESPONSE ===")
    print(final_answer)
