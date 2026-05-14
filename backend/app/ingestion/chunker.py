import base64
import io
import json
import logging
from docling.chunking import HierarchicalChunker
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class DataChunker:
    def __init__(self):
        self.chunker = HierarchicalChunker()

    def process_and_chunk(self, doc) -> list[Document]:
        logger.info("Starting Hierarchical Chunking (Chunk by Title)...")
        
        # 1. Create the chunks based on document layout and headings
        raw_chunks = list(self.chunker.chunk(doc))
        logger.info(f"Created {len(raw_chunks)} semantic chunks.")

        documents = []

        # 2. Iterate through chunks to extract mixed content (Text, Tables, Images)
        for i, chunk in enumerate(raw_chunks):
            chunk_data = {
                "text": chunk.text,
                "tables": [],
                "images": [],
                "types": ["text"]
            }

            # Check if this chunk contains any tables
            if chunk.meta.doc_items:
                for item in chunk.meta.doc_items:
                    # If it's a table, export to HTML
                    if hasattr(item, 'export_to_html'):
                        chunk_data["types"].append("table")
                        chunk_data["tables"].append(item.export_to_html(doc))
                    
                    # If it's a picture, export to Base64
                    elif hasattr(item, 'image') and item.image:
                        chunk_data["types"].append("image")
                        buffered = io.BytesIO()
                        item.image.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        chunk_data["images"].append(img_str)

            # De-duplicate the types list
            chunk_data["types"] = list(set(chunk_data["types"]))

            # 3. Create the LangChain Document with metadata
            metadata = {
                "chunk_id": i + 1,
                "types": chunk_data["types"],
                "original_content": json.dumps({
                    "raw_text": chunk_data["text"],
                    "tables_html": chunk_data["tables"],
                    "images_base64": chunk_data["images"]
                })
            }

            lc_doc = Document(
                page_content=chunk_data["text"], # Will be replaced by AI summary later
                metadata=metadata
            )
            documents.append(lc_doc)

        return documents

