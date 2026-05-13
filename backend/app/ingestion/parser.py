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
    def process_document(self, file_path: str):
        logger.info(f"Processing document with Docling: {file_path}")
        try:
            result = self.converter.convert(file_path)
            return result.document # Return the raw document for the chunker!
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