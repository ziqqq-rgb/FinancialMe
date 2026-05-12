import logging
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import CompositeElement, Table, Image

logger = logging.getLogger(__name__)

class document_parser:
    def __init__(self):
        pass

    def process_document(self, file_path: str) -> dict[str, list]:
        logger.info(f"Processing document: {file_path}")

        try:
            raw_elements = partition_pdf(
                filename=file_path,
                strategy="hi_res",                  
                infer_table_structure=True,        
                extract_image_block_types=["Image"],
                extract_image_block_to_payload=True,
                chunking_strategy="by_title",       
                max_characters=4000,
                new_after_n_characters=3800,
                combine_text_under_n_characters=2000
            )

        except Exception as e:
            logger.error(f"failed processing document: {str(e)}")
            raise e
        
        categorized_elements = {
            "text": [],
            "tables": [],
            "images": [] 
        }

        for element in raw_elements:

            if isinstance(element, CompositeElement):
                categorized_elements["text"].append(element.text)

            elif isinstance(element, Table):
                html_table = element.metadata.text_as_html if hasattr(element.metadata, "text_as_html") else element.text
                categorized_elements["tables"].append(html_table)
            
            if hasattr(element.metadata, "image_base64") and element.metadata.image_base64:
                categorized_elements["images"].append(element.metadata.image_base64)
        
        logger.info(f"Extraction complete: {len(categorized_elements['text'])} text blocks, "
                    f"{len(categorized_elements['tables'])} tables, {len(categorized_elements['images'])} images.")
        
        return categorized_elements
    
file_path = "./data/sample1.pdf"
parser = document_parser()
result = parser.process_document(file_path)
print(result)