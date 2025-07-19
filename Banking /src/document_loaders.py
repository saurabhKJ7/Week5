"""
Advanced Document Loaders for Banking Knowledge Base
Handles complex banking documents with tables, rate sheets, and compliance matrices
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
from io import StringIO

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader
from langchain_community.document_loaders import DirectoryLoader

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TableContext:
    """Context information for preserving table relationships"""
    table_id: str
    table_title: Optional[str]
    headers: List[str]
    preceding_context: str
    following_context: str
    page_number: int

@dataclass
class CrossReference:
    """Cross-reference information found in documents"""
    reference_text: str
    reference_type: str  # "table", "section", "figure", etc.
    target_id: Optional[str]
    source_location: str

class BankingDocumentLoader:
    """
    Advanced document loader for banking documents with table and reference preservation
    """
    
    def __init__(
        self,
        preserve_tables: bool = True,
        handle_cross_references: bool = True,
        extract_rate_sheets: bool = True,
        preserve_compliance_matrices: bool = True
    ):
        self.preserve_tables = preserve_tables
        self.handle_cross_references = handle_cross_references
        self.extract_rate_sheets = extract_rate_sheets
        self.preserve_compliance_matrices = preserve_compliance_matrices
        
        # Pattern matching for banking-specific elements
        self.table_patterns = [
            r"Table\s+(\d+\.?\d*)[:\s]+(.+?)(?=\n\n|\n[A-Z]|\Z)",
            r"Rate\s+Sheet[:\s]+(.+?)(?=\n\n|\n[A-Z]|\Z)",
            r"Compliance\s+Matrix[:\s]+(.+?)(?=\n\n|\n[A-Z]|\Z)"
        ]
        
        self.cross_ref_patterns = [
            r"(?:see|refer to|as shown in)\s+table\s+(\d+\.?\d*)",
            r"(?:see|refer to|as shown in)\s+section\s+(\d+\.?\d*)",
            r"(?:see|refer to|as shown in)\s+appendix\s+([A-Z]+)",
            r"(?:see|refer to|as shown in)\s+figure\s+(\d+\.?\d*)"
        ]

    def load_documents(self, file_path: str) -> List[Document]:
        """
        Load and process banking documents with advanced structure preservation
        """
        documents = []
        file_path = Path(file_path)
        
        if file_path.is_file():
            documents.extend(self._load_single_file(file_path))
        elif file_path.is_dir():
            documents.extend(self._load_directory(file_path))
        else:
            raise ValueError(f"Invalid file path: {file_path}")
        
        return documents
    
    def _load_directory(self, dir_path: Path) -> List[Document]:
        """Load all supported documents from directory"""
        documents = []
        supported_extensions = ['.pdf', '.docx', '.txt']
        
        for ext in supported_extensions:
            pattern = f"*{ext}"
            files = list(dir_path.glob(pattern))
            
            for file_path in files:
                try:
                    logger.info(f"Processing file: {file_path}")
                    docs = self._load_single_file(file_path)
                    documents.extend(docs)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue
        
        return documents
    
    def _load_single_file(self, file_path: Path) -> List[Document]:
        """Load and process a single file"""
        if file_path.suffix.lower() == '.pdf':
            return self._load_pdf(file_path)
        elif file_path.suffix.lower() == '.txt':
            return self._load_text(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return []
    
    def _load_pdf(self, file_path: Path) -> List[Document]:
        """Load PDF with advanced table and structure preservation"""
        documents = []
        
        try:
            # Try unstructured loader first for better table extraction
            loader = UnstructuredPDFLoader(
                str(file_path),
                mode="elements",
                strategy="hi_res"  # High resolution for better table detection
            )
            raw_documents = loader.load()
            
            # If unstructured fails, fallback to PyPDF
            if not raw_documents:
                loader = PyPDFLoader(str(file_path))
                raw_documents = loader.load()
            
        except Exception as e:
            logger.warning(f"Unstructured PDF loading failed, using PyPDF: {e}")
            loader = PyPDFLoader(str(file_path))
            raw_documents = loader.load()
        
        # Process each page
        table_contexts = []
        cross_references = []
        
        for page_num, doc in enumerate(raw_documents):
            # Extract tables and their contexts
            if self.preserve_tables:
                page_tables = self._extract_table_contexts(doc.page_content, page_num)
                table_contexts.extend(page_tables)
            
            # Extract cross-references
            if self.handle_cross_references:
                page_refs = self._extract_cross_references(doc.page_content, page_num)
                cross_references.extend(page_refs)
            
            # Create enhanced document with preserved structure
            enhanced_doc = self._create_enhanced_document(
                doc,
                file_path.name,
                page_num,
                table_contexts,
                cross_references
            )
            documents.append(enhanced_doc)
        
        # Post-process to resolve cross-references
        if cross_references:
            documents = self._resolve_cross_references(documents, cross_references, table_contexts)
        
        return documents
    
    def _load_text(self, file_path: Path) -> List[Document]:
        """Load text file with structure preservation"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        doc = Document(
            page_content=content,
            metadata={
                "source": str(file_path),
                "file_type": "text",
                "total_pages": 1
            }
        )
        
        return [doc]
    
    def _extract_table_contexts(self, text: str, page_num: int) -> List[TableContext]:
        """Extract tables with their surrounding context"""
        table_contexts = []
        
        for i, pattern in enumerate(self.table_patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                # Extract table information
                if len(match.groups()) >= 2:
                    table_id = match.group(1) if match.group(1) else f"table_{i}_{page_num}"
                    table_title = match.group(2) if len(match.groups()) > 1 else None
                else:
                    table_id = f"table_{i}_{page_num}"
                    table_title = match.group(1) if match.groups() else None
                
                # Get surrounding context
                start_pos = max(0, match.start() - 200)
                end_pos = min(len(text), match.end() + 200)
                
                preceding_context = text[start_pos:match.start()].strip()
                following_context = text[match.end():end_pos].strip()
                
                # Try to extract table headers
                table_content = match.group(0)
                headers = self._extract_table_headers(table_content)
                
                table_context = TableContext(
                    table_id=table_id,
                    table_title=table_title,
                    headers=headers,
                    preceding_context=preceding_context,
                    following_context=following_context,
                    page_number=page_num
                )
                
                table_contexts.append(table_context)
        
        return table_contexts
    
    def _extract_table_headers(self, table_text: str) -> List[str]:
        """Extract headers from table text"""
        lines = table_text.split('\n')
        headers = []
        
        for line in lines:
            # Look for lines that might be headers (contain | or multiple spaces)
            if '|' in line or re.search(r'\s{2,}', line):
                # Split by | or multiple spaces
                if '|' in line:
                    potential_headers = [h.strip() for h in line.split('|') if h.strip()]
                else:
                    potential_headers = [h.strip() for h in re.split(r'\s{2,}', line) if h.strip()]
                
                # If this looks like headers (multiple short words), use it
                if len(potential_headers) > 1 and all(len(h) < 50 for h in potential_headers):
                    headers = potential_headers
                    break
        
        return headers
    
    def _extract_cross_references(self, text: str, page_num: int) -> List[CrossReference]:
        """Extract cross-references from text"""
        cross_references = []
        
        for pattern in self.cross_ref_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                ref_type = "table" if "table" in pattern else \
                          "section" if "section" in pattern else \
                          "appendix" if "appendix" in pattern else "figure"
                
                cross_ref = CrossReference(
                    reference_text=match.group(0),
                    reference_type=ref_type,
                    target_id=match.group(1),
                    source_location=f"page_{page_num}_{match.start()}"
                )
                
                cross_references.append(cross_ref)
        
        return cross_references
    
    def _create_enhanced_document(
        self,
        original_doc: Document,
        filename: str,
        page_num: int,
        table_contexts: List[TableContext],
        cross_references: List[CrossReference]
    ) -> Document:
        """Create enhanced document with preserved structure metadata"""
        
        enhanced_metadata = {
            **original_doc.metadata,
            "filename": filename,
            "page_number": page_num,
            "document_type": "banking_document",
            "has_tables": len(table_contexts) > 0,
            "has_cross_references": len(cross_references) > 0,
            "processing_timestamp": pd.Timestamp.now().isoformat()
        }
        
        # Add table information to metadata
        if table_contexts:
            enhanced_metadata["tables"] = [
                {
                    "table_id": tc.table_id,
                    "table_title": tc.table_title,
                    "headers": tc.headers
                }
                for tc in table_contexts if tc.page_number == page_num
            ]
        
        # Add cross-reference information to metadata
        if cross_references:
            enhanced_metadata["cross_references"] = [
                {
                    "reference_text": cr.reference_text,
                    "reference_type": cr.reference_type,
                    "target_id": cr.target_id
                }
                for cr in cross_references
            ]
        
        # Enhanced content with table contexts preserved
        enhanced_content = original_doc.page_content
        
        # Add table context information to content if enabled
        if self.preserve_tables and table_contexts:
            page_tables = [tc for tc in table_contexts if tc.page_number == page_num]
            if page_tables:
                table_info = "\n\n=== TABLE CONTEXT INFORMATION ===\n"
                for tc in page_tables:
                    table_info += f"\nTable {tc.table_id}: {tc.table_title or 'No title'}\n"
                    if tc.headers:
                        table_info += f"Headers: {', '.join(tc.headers)}\n"
                    table_info += f"Preceding context: {tc.preceding_context[:100]}...\n"
                
                enhanced_content = enhanced_content + table_info
        
        return Document(
            page_content=enhanced_content,
            metadata=enhanced_metadata
        )
    
    def _resolve_cross_references(
        self,
        documents: List[Document],
        cross_references: List[CrossReference],
        table_contexts: List[TableContext]
    ) -> List[Document]:
        """Resolve cross-references and add context"""
        
        # Create lookup tables for references
        table_lookup = {tc.table_id: tc for tc in table_contexts}
        
        enhanced_documents = []
        
        for doc in documents:
            enhanced_content = doc.page_content
            
            # Process cross-references in this document
            doc_refs = doc.metadata.get("cross_references", [])
            
            for ref in doc_refs:
                if ref["reference_type"] == "table" and ref["target_id"] in table_lookup:
                    table_context = table_lookup[ref["target_id"]]
                    
                    # Add resolved table context
                    context_info = f"\n\n[CROSS-REFERENCE CONTEXT for {ref['reference_text']}]\n"
                    context_info += f"Table {table_context.table_id}: {table_context.table_title}\n"
                    if table_context.headers:
                        context_info += f"Table headers: {', '.join(table_context.headers)}\n"
                    context_info += f"Context: {table_context.preceding_context[:200]}...\n"
                    
                    enhanced_content += context_info
            
            # Create enhanced document
            enhanced_doc = Document(
                page_content=enhanced_content,
                metadata=doc.metadata
            )
            enhanced_documents.append(enhanced_doc)
        
        return enhanced_documents

# Convenience function for easy usage
def load_banking_documents(
    file_path: str,
    preserve_tables: bool = True,
    handle_cross_references: bool = True,
    extract_rate_sheets: bool = True
) -> List[Document]:
    """
    Load banking documents with advanced structure preservation
    
    Args:
        file_path: Path to file or directory
        preserve_tables: Whether to preserve table context
        handle_cross_references: Whether to handle cross-references
        extract_rate_sheets: Whether to extract rate sheet information
    
    Returns:
        List of processed Document objects
    """
    loader = BankingDocumentLoader(
        preserve_tables=preserve_tables,
        handle_cross_references=handle_cross_references,
        extract_rate_sheets=extract_rate_sheets
    )
    
    return loader.load_documents(file_path)

# Example usage
if __name__ == "__main__":
    # Example: Load documents from the Documents directory
    documents_path = Path(__file__).parent.parent / "Documents"
    
    if documents_path.exists():
        print(f"Loading banking documents from: {documents_path}")
        documents = load_banking_documents(str(documents_path))
        
        print(f"Loaded {len(documents)} document chunks")
        
        for i, doc in enumerate(documents[:2]):  # Show first 2 documents
            print(f"\n--- Document {i+1} ---")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"Page: {doc.metadata.get('page_number', 'N/A')}")
            print(f"Has tables: {doc.metadata.get('has_tables', False)}")
            print(f"Content preview: {doc.page_content[:200]}...")
    else:
        print(f"Documents directory not found: {documents_path}") 