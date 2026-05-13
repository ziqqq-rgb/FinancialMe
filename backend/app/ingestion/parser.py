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
    import os
    
    # 1. Find the path to the PDF
    sample_path = "./sample1.pdf"
    
    if os.path.exists(sample_path):
        print(f"Found PDF at: {sample_path}")
        print("Starting Docling Parser... (This might take a few seconds)")
        
        # 2. Run the Parser
        parser = document_parser()
        doc = parser.process_document(sample_path)
        
        # 3. Verify the output
        print("\n=== PARSE SUCCESSFUL ===")
        
        # Print some stats to prove it worked
        all_items = list(doc.iterate_items())
        print(f"Total semantic items found: {len(all_items)}")
        print(f"Total pictures extracted: {len(doc.pictures)}")
        print(f"Total tables extracted: {len(doc.tables)}") # <--- ADD THIS LINE
        
        # Print a tiny preview of the Markdown conversion to prove the text is there
        markdown_preview = doc.export_to_markdown()
        print("\n--- Content Preview (First 300 chars) ---")
        print(markdown_preview[:300] + "...\n")
        
    else:
        print(f"ERROR: Could not find PDF at {sample_path}")
        print("Make sure your sample1.pdf is in the backend/data/ folder!")