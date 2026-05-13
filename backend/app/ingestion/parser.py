import base64
import logging
import io
import os
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling_core.types.doc import TableItem, TextItem

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class document_parser:
    def __init__(self):
        # 1. Configure Docling for High-Res Extraction
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        pipeline_options.do_ocr = True  # Handles text in images/scans
        pipeline_options.generate_page_images = False # We want pictures, not whole pages
        pipeline_options.generate_picture_images = True  # Enable picture extraction



        # 2. Setup the converter with the correct PDF options
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def process_document(self, file_path: str) -> dict:
        logger.info(f"Processing document with Docling: {file_path}")
        
        try:
            # Convert the document
            result = self.converter.convert(file_path)
            doc = result.document
            
            categorized_elements = {
                "text": [],
                "tables": [],
                "images": []
            }

            # 3. Categorize Elements
            # We iterate through the document items to find text and tables
            for element, _level in doc.iterate_items():
                
                # Extract Tables as HTML (matching your previous strategy)
                if isinstance(element, TableItem):
                    html_table = element.export_to_html(doc)
                    categorized_elements["tables"].append(html_table)
                
                # Extract Text blocks
                elif isinstance(element, TextItem):
                    categorized_elements["text"].append(element.text)

            # 4. Extract Images (Pictures) as Base64
            # Docling stores extracted figures in the 'pictures' attribute
            for i, picture in enumerate(doc.pictures):
                # 1. Use get_image(doc) to retrieve the actual PIL image object
                pil_image = picture.get_image(doc)
                
                if pil_image:
                    buffered = io.BytesIO()
                    # 2. Now you can call .save() because pil_image is a real PIL object
                    pil_image.save(buffered, format="PNG")
                    
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    categorized_elements["images"].append(img_str)

            logger.info(f"Extraction complete: {len(categorized_elements['text'])} text, "
                        f"{len(categorized_elements['tables'])} tables, "
                        f"{len(categorized_elements['images'])} images.")
            
            return categorized_elements

        except Exception as e:
            logger.error(f"Docling failed to process: {str(e)}")
            raise e

# --- Test run ---
if __name__ == "__main__":
   sample_path = "./sample1.pdf" 
    
if os.path.exists(sample_path):
        parser = document_parser()
        res = parser.process_document(sample_path)
        
        # Verify output
        print(f"\nSuccessfully parsed {len(res['text'])} text blocks.")
        if res['tables']:
            print(f"Captured {len(res['tables'])} tables as HTML.")
        if res['images']:
            print(f"Extracted {len(res['images'])} images as Base64 strings.")
else:
    print(f"Error: Could not find PDF at {sample_path}")