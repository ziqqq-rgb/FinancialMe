import os
import json
import logging
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document

# Load your API Keys
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)

class ContentSummarizer:
    def __init__(self):
    
        self.model = ChatOpenAI(
            model="gpt-4o", 
            base_url="https://models.github.ai/inference", 
            api_key=api_key
            )

    def summarize_chunk(self, chunk: Document) -> Document:
        
        types = chunk.metadata.get("types", [])
        
        if "table" not in types and "image" not in types:
            return chunk

        logger.info(f"Summarizing visual content for Chunk ID: {chunk.metadata['chunk_id']}...")
        
        # 1. Unpack the original data from the metadata backpack
        content_dict = json.loads(chunk.metadata["original_content"])
        
        # 2. Prepare the message for the AI
        messages = [
            {"type": "text", 
             "text": 
             "You are an expert data analyst. "
             "I will provide you with the text context, "
             "and potentially some HTML tables and images from a document section. "
             "Your job is to write a highly searchable, concise summary of the visual data (tables/images) presented."
             "Do not summarize the text, just describe what the tables and images show."}
        ]

        # Add the surrounding text for context (helps the AI understand the charts/tables)
        if content_dict["raw_text"]:
            messages.append({"type": "text", "text": f"Context Text:\n{content_dict['raw_text']}"})

        # Add all HTML tables to the prompt
        for html_table in content_dict.get("tables_html", []):
            messages.append({"type": "text", "text": f"HTML Table Data:\n{html_table}"})

        # Add all Base64 images to the prompt
        for img_base64 in content_dict.get("images_base64", []):
            messages.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
            })

        # 3. Call GPT-4o to generate the summary
        try:
            ai_response = self.model.invoke([HumanMessage(content=messages)])
            visual_summary = ai_response.content
            
            # 4. Append the new AI summary to the chunk's page_content
            # This ensures the Vector Store will index both the original text AND the visual summary
            chunk.page_content = f"{chunk.page_content}\n\n[AI Visual Summary]: {visual_summary}"
            
        except Exception as e:
            logger.error(f"Failed to summarize chunk {chunk.metadata['chunk_id']}: {str(e)}")

        return chunk

    def process_all_chunks(self, chunks: List[Document]) -> List[Document]:
        """Runs the summarizer over the entire list of chunks."""
        logger.info(f"Starting summarization for {len(chunks)} chunks...")
        summarized_chunks = []
        
        for i, chunk in enumerate(chunks):
            # We process them one by one. (In a production app, you might use asyncio/batching here)
            updated_chunk = self.summarize_chunk(chunk)
            summarized_chunks.append(updated_chunk)
            
        logger.info("Summarization complete!")
        return summarized_chunks

