import logging
import os
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

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

