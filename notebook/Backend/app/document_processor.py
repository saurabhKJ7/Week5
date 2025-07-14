from typing import Dict, Any, Tuple
from pathlib import Path
import logging
import json

# Main parsing engine for most file types
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json
import pytesseract
# Specialized parsers for structured data and high-quality PDF extraction
import pandas as pd
import nbformat
import pdfplumber
import base64
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    A hybrid document processor that uses specialized parsers for common,
    structured formats and falls back to the powerful 'unstructured' library
    for a wide range of other document types.
    """

    def __init__(self, temp_image_dir: str = "temp_images") -> None:
        """Initializes the processor and maps file extensions to custom handlers."""
        self.temp_image_dir = temp_image_dir
        if not os.path.exists(self.temp_image_dir):
            os.makedirs(self.temp_image_dir)
            
        self.custom_handlers: Dict[str, Any] = {
            '.pdf': self._process_pdf,
            '.csv': self._process_csv_excel,
            '.xls': self._process_csv_excel,
            '.xlsx': self._process_csv_excel,
            '.json': self._process_json,
            '.ipynb': self._process_notebook,
        }

    def process_file(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Processes a file by routing it to the appropriate parser.

        Args:
            file_path: The path to the file to be processed.

        Returns:
            A tuple containing the extracted text content and a metadata dictionary.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            extension = path.suffix.lower()

            if extension in self.custom_handlers:
                # Route to a specialized, high-control parser
                return self.custom_handlers[extension](path)
            else:
                # Use 'unstructured' for broad format support (DOCX, PPTX, HTML, etc.)
                return self._process_with_unstructured(path)
        except Exception as e:
            logger.error(f"Failed to process file {file_path}. Error: {str(e)}")
            raise

    def _process_with_unstructured(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Processes a file using the 'unstructured' library, which is excellent
        for a wide variety of formats like DOCX, PPTX, HTML, and images.
        """
        logger.info(f"Processing '{file_path.name}' with unstructured...")
        try:
            # Note: Image processing requires OCR dependencies like Tesseract.
            # If not installed, this step may fail for image files.
            # See: https://unstructured-io.github.io/unstructured/installing.html
            raw_elements = partition(filename=str(file_path), strategy="hi_res")
            
            # Chunk by title to preserve hierarchy
            chunks = chunk_by_title(raw_elements)

            structured_chunks = []
            for chunk in chunks:
                chunk_metadata = chunk.metadata.to_dict()
                
                # Add section title if available
                section = chunk_metadata.get('section')
                
                meta = {
                    "content": chunk.text, # Include the content
                    "type": file_path.suffix.lstrip('.').lower(),
                    "filename": file_path.name,
                    "source": "unstructured",
                    "section": section if section else "Unknown"
                }
                structured_chunks.append(meta)

            # For now, we'll join the content, but we'll adapt the pipeline to handle discrete chunks
            content = "\n\n".join([chunk.text for chunk in chunks])
            
            # Handle images by saving them and adding placeholders
            image_paths = []
            for el in raw_elements: # Iterate over raw_elements for images
                if el.category == "Image":
                    # Ensure image data and mime type are available
                    if hasattr(el.metadata, 'image_base64') and hasattr(el.metadata, 'image_mime_type'):
                        image_data = el.metadata.image_base64
                        mime_type = el.metadata.image_mime_type
                        
                        if image_data and mime_type:
                            image_format = mime_type.split('/')[-1]
                            image_filename = f"{Path(file_path).stem}_{len(image_paths)}.{image_format}"
                            image_path = os.path.join(self.temp_image_dir, image_filename)
                            
                            with open(image_path, "wb") as img_file:
                                img_file.write(base64.b64decode(image_data))
                            image_paths.append(image_path)
            
            # We're returning a single content string for now, but the metadata list
            # holds the structured info. We'll adapt the RAG pipeline to use this.
            final_metadata = {
                "type": file_path.suffix.lstrip('.').lower(),
                "filename": file_path.name,
                "source": "unstructured",
                "num_elements": len(raw_elements),
                "images": image_paths,
                "structured_chunks": structured_chunks # Store the list of chunk metadata
            }
            
            return content, final_metadata
        except Exception as e:
            logger.error(f"Unstructured processing failed for {file_path}. Error: {e}")
            raise

    # --- Custom Handlers for Specialized Formats ---

    def _process_pdf(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Processes a PDF using pdfplumber. If it fails, it falls back to unstructured.
        """
        logger.info(f"Processing PDF '{file_path.name}' with pdfplumber...")
        try:
            with pdfplumber.open(file_path) as pdf:
                pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
                content = "\n".join(pages)
                metadata = {
                    "type": "pdf",
                    "filename": file_path.name,
                    "source": "pdfplumber",
                    "pages": len(pdf.pages),
                }
                if not content.strip():
                    metadata["warning"] = "pdfplumber extracted no text."
                return content, metadata
        except Exception as e:
            logger.warning(f"pdfplumber failed for {file_path}: {e}. Falling back to unstructured.")
            return self._process_with_unstructured(file_path)

    def _process_csv_excel(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Processes CSV and Excel files into a string format using pandas."""
        logger.info(f"Processing Table '{file_path.name}' with pandas...")
        try:
            df = pd.read_excel(file_path) if file_path.suffix.lower() in ['.xls', '.xlsx'] else pd.read_csv(file_path)
            content = df.to_string()
            metadata = {
                "type": file_path.suffix.lstrip('.').lower(),
                "filename": file_path.name,
                "source": "pandas",
                "rows": len(df),
                "columns": list(df.columns),
            }
            if df.empty:
                metadata["warning"] = "The table file is empty."
            return content, metadata
        except Exception as e:
            logger.error(f"Pandas processing failed for {file_path}. Error: {e}")
            raise

    def _process_json(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Processes a JSON file by loading and re-dumping it as a string."""
        logger.info(f"Processing JSON '{file_path.name}'...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, indent=2), {
                "type": "json",
                "filename": file_path.name,
                "source": "json_module",
            }
        except Exception as e:
            logger.error(f"JSON processing failed for {file_path}. Error: {e}")
            raise

    def _process_notebook(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Processes Jupyter Notebooks, extracting content from markdown and code cells."""
        logger.info(f"Processing Notebook '{file_path.name}' with nbformat...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            cells = []
            for cell in nb.cells:
                if cell.cell_type == 'markdown':
                    cells.append(cell.source)
                elif cell.cell_type == 'code':
                    cells.append(f"```python\n{cell.source}\n```")
            
            content = "\n\n".join(cells)
            metadata = {
                "type": "notebook",
                "filename": file_path.name,
                "source": "nbformat",
                "cells": len(nb.cells),
            }
            if not content.strip():
                metadata["warning"] = "No content found in notebook cells."
            return content, metadata
        except Exception as e:
            logger.error(f"Jupyter notebook processing failed for {file_path}. Error: {e}")
            raise 