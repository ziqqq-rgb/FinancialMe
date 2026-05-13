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

# --- Integration Test ---
if __name__ == "__main__":
    from parser import document_parser

    logging.basicConfig(level=logging.INFO)
    
    # 1. Parse (returns the raw Docling 'doc' object now)
    sample_path = "./sample1.pdf"
    
    parser = document_parser()
    # Note: You will need to modify your parser.py to return 'result.document' 
    # instead of the sorted dictionary, so the chunker can use it!
    doc = parser.process_document(sample_path)

    # 2. Chunk by Title
    chunker = DataChunker()
    chunks = chunker.process_and_chunk(doc)

    # 3. Verify exactly like the teacher's output
    for i, chunk in enumerate(chunks[:5]):
        print(f"\nProcessing chunk {i+1}/{len(chunks)}")
        print(f"Types found: {chunk.metadata['types']}")
        content_dict = json.loads(chunk.metadata["original_content"])
        print(f"Tables: {len(content_dict['tables_html'])}, Images: {len(content_dict['images_base64'])}")