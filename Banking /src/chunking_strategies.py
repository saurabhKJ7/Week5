"""
Advanced Chunking Strategies for Banking RAG System
Addresses key challenges: Table Context Loss, Cross-Reference Failures, Inconsistent Responses
"""

import re
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter
)
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

from src.config import get_settings

settings = get_settings()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChunkMetadata:
    """Enhanced metadata for chunks with banking-specific information"""
    chunk_id: str
    source_document: str
    chunk_index: int
    total_chunks: int
    chunk_type: str  # "text", "table", "rate_sheet", "compliance_matrix"
    contains_table: bool
    table_references: List[str]
    cross_references: List[str]
    preceding_context: str
    following_context: str
    semantic_topic: Optional[str]
    compliance_relevant: bool

class BankingChunker(ABC):
    """Abstract base class for banking document chunkers"""
    
    @abstractmethod
    def chunk_document(self, document: Document) -> List[Document]:
        """Chunk a single document"""
        pass
    
    @abstractmethod
    def get_chunker_type(self) -> str:
        """Get the type identifier for this chunker"""
        pass

class TablePreservingChunker(BankingChunker):
    """
    Chunker that preserves table context and relationships
    Solves: Table Context Loss challenge
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        preserve_table_integrity: bool = True,
        table_context_window: int = 300
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_table_integrity = preserve_table_integrity
        self.table_context_window = table_context_window
        
        # Base splitter for non-table content
        self.base_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Patterns to identify tables and rate sheets
        self.table_patterns = [
            r"(?i)table\s+\d+\.?\d*[:\s]+.+?(?=\n\n|\n[A-Z]|\Z)",
            r"(?i)rate\s+sheet[:\s]+.+?(?=\n\n|\n[A-Z]|\Z)",
            r"(?i)compliance\s+matrix[:\s]+.+?(?=\n\n|\n[A-Z]|\Z)",
            r"\|.*\|.*\|",  # Pipe-separated tables
            r"^\s*\w+\s+\w+\s+\w+\s*$",  # Multi-column layouts
        ]
    
    def get_chunker_type(self) -> str:
        return "table_preserving"
    
    def chunk_document(self, document: Document) -> List[Document]:
        """Chunk document while preserving table integrity"""
        content = document.page_content
        metadata = document.metadata
        
        # Identify table regions
        table_regions = self._identify_table_regions(content)
        
        if not table_regions:
            # No tables found, use standard chunking
            return self._standard_chunk(document)
        
        # Process content with table preservation
        chunks = []
        processed_regions = []
        
        for table_region in table_regions:
            # Create table-aware chunks
            table_chunks = self._create_table_chunks(
                content, table_region, metadata
            )
            chunks.extend(table_chunks)
            processed_regions.append(table_region)
        
        # Process remaining non-table content
        remaining_chunks = self._process_non_table_content(
            content, processed_regions, metadata
        )
        chunks.extend(remaining_chunks)
        
        return self._post_process_chunks(chunks)
    
    def _identify_table_regions(self, content: str) -> List[Dict[str, Any]]:
        """Identify regions containing tables or structured data"""
        table_regions = []
        
        for pattern in self.table_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                # Extend region to include context
                start = max(0, match.start() - self.table_context_window)
                end = min(len(content), match.end() + self.table_context_window)
                
                # Look for table title or header
                pre_context = content[start:match.start()]
                table_title = self._extract_table_title(pre_context, content[match.start():match.end()])
                
                region = {
                    "start": start,
                    "end": end,
                    "table_start": match.start(),
                    "table_end": match.end(),
                    "content": content[start:end],
                    "table_content": content[match.start():match.end()],
                    "title": table_title,
                    "type": self._classify_table_type(content[match.start():match.end()])
                }
                
                table_regions.append(region)
        
        # Merge overlapping regions
        return self._merge_overlapping_regions(table_regions)
    
    def _extract_table_title(self, pre_context: str, table_content: str) -> Optional[str]:
        """Extract table title from context"""
        # Look for table titles in preceding lines
        lines = pre_context.split('\n')[-3:]  # Last 3 lines before table
        
        for line in reversed(lines):
            line = line.strip()
            if line and not re.match(r'^\d+\.$', line):  # Not just a number
                # Check if it looks like a title
                if len(line) < 200 and any(keyword in line.lower() for keyword in 
                    ['table', 'rate', 'schedule', 'matrix', 'sheet']):
                    return line
        
        # Try to find title in table content
        table_lines = table_content.split('\n')[:3]
        for line in table_lines:
            line = line.strip()
            if line and len(line) < 200 and not re.match(r'^[\|\s\-\+]+$', line):
                return line
        
        return None
    
    def _classify_table_type(self, table_content: str) -> str:
        """Classify the type of table based on content"""
        content_lower = table_content.lower()
        
        if any(keyword in content_lower for keyword in ['rate', 'apr', 'interest', '%']):
            return "rate_sheet"
        elif any(keyword in content_lower for keyword in ['compliance', 'regulation', 'requirement']):
            return "compliance_matrix"
        elif any(keyword in content_lower for keyword in ['amortization', 'payment', 'balance']):
            return "amortization_table"
        else:
            return "general_table"
    
    def _merge_overlapping_regions(self, regions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping table regions"""
        if not regions:
            return []
        
        # Sort by start position
        regions.sort(key=lambda x: x["start"])
        
        merged = [regions[0]]
        
        for current in regions[1:]:
            last_merged = merged[-1]
            
            # Check for overlap
            if current["start"] <= last_merged["end"]:
                # Merge regions
                merged[-1] = {
                    "start": last_merged["start"],
                    "end": max(last_merged["end"], current["end"]),
                    "table_start": min(last_merged["table_start"], current["table_start"]),
                    "table_end": max(last_merged["table_end"], current["table_end"]),
                    "content": last_merged["content"] + "\n" + current["content"],
                    "table_content": last_merged["table_content"] + "\n" + current["table_content"],
                    "title": last_merged["title"] or current["title"],
                    "type": "mixed" if last_merged["type"] != current["type"] else last_merged["type"]
                }
            else:
                merged.append(current)
        
        return merged
    
    def _create_table_chunks(
        self, 
        content: str, 
        table_region: Dict[str, Any], 
        base_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Create chunks that preserve table integrity"""
        chunks = []
        region_content = table_region["content"]
        
        # For small tables, keep entire table with context in one chunk
        if len(region_content) <= self.chunk_size:
            chunk_metadata = {
                **base_metadata,
                "chunk_type": "table_with_context",
                "table_type": table_region["type"],
                "table_title": table_region["title"],
                "contains_table": True,
                "table_preserved": True
            }
            
            chunk = Document(
                page_content=region_content,
                metadata=chunk_metadata
            )
            chunks.append(chunk)
        
        else:
            # For large tables, create strategic splits
            table_content = table_region["table_content"]
            pre_context = region_content[:table_region["table_start"] - table_region["start"]]
            post_context = region_content[table_region["table_end"] - table_region["start"]:]
            
            # Split table by logical sections (rows, columns, or headers)
            table_sections = self._split_table_by_structure(table_content)
            
            for i, section in enumerate(table_sections):
                # Add context to each section
                chunk_content = pre_context + "\n\n" + section
                if i == len(table_sections) - 1:  # Last section gets post context
                    chunk_content += "\n\n" + post_context
                
                chunk_metadata = {
                    **base_metadata,
                    "chunk_type": "table_section",
                    "table_type": table_region["type"],
                    "table_title": table_region["title"],
                    "table_section": i + 1,
                    "total_table_sections": len(table_sections),
                    "contains_table": True,
                    "table_preserved": True
                }
                
                chunk = Document(
                    page_content=chunk_content,
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
        
        return chunks
    
    def _split_table_by_structure(self, table_content: str) -> List[str]:
        """Split table content by logical structure"""
        lines = table_content.split('\n')
        sections = []
        current_section = []
        header_found = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a header line
            is_header = (
                not header_found and 
                (re.match(r'^[\|\s\-\+]+$', line) or  # Separator line
                 len([c for c in line if c.isalpha()]) > len([c for c in line if c.isdigit()]))  # More letters than numbers
            )
            
            if is_header and not header_found:
                current_section.append(line)
                header_found = True
            elif len('\n'.join(current_section + [line])) > self.chunk_size * 0.8:
                # Section getting too large, split it
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections if sections else [table_content]
    
    def _process_non_table_content(
        self, 
        content: str, 
        table_regions: List[Dict[str, Any]], 
        base_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process content that doesn't contain tables"""
        # Extract non-table content
        non_table_content = []
        last_end = 0
        
        for region in sorted(table_regions, key=lambda x: x["start"]):
            if region["start"] > last_end:
                non_table_content.append(content[last_end:region["start"]])
            last_end = region["end"]
        
        # Add remaining content after last table
        if last_end < len(content):
            non_table_content.append(content[last_end:])
        
        # Chunk non-table content normally
        chunks = []
        for section in non_table_content:
            if section.strip():
                section_doc = Document(page_content=section, metadata=base_metadata)
                section_chunks = self.base_splitter.split_documents([section_doc])
                
                for chunk in section_chunks:
                    chunk.metadata.update({
                        "chunk_type": "text",
                        "contains_table": False,
                        "table_preserved": False
                    })
                
                chunks.extend(section_chunks)
        
        return chunks
    
    def _standard_chunk(self, document: Document) -> List[Document]:
        """Standard chunking for documents without tables"""
        chunks = self.base_splitter.split_documents([document])
        
        for chunk in chunks:
            chunk.metadata.update({
                "chunk_type": "text",
                "contains_table": False,
                "table_preserved": False
            })
        
        return chunks
    
    def _post_process_chunks(self, chunks: List[Document]) -> List[Document]:
        """Post-process chunks to add final metadata and numbering"""
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_index": i,
                "total_chunks": total_chunks,
                "chunker_type": self.get_chunker_type()
            })
        
        return chunks

class CrossReferenceChunker(BankingChunker):
    """
    Chunker that resolves and preserves cross-references
    Solves: Cross-Reference Failures challenge
    """
    
    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 300,
        resolve_references: bool = True,
        reference_context_window: int = 500
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.resolve_references = resolve_references
        self.reference_context_window = reference_context_window
        
        self.base_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Cross-reference patterns
        self.reference_patterns = [
            (r"(?i)(?:see|refer to|as shown in|according to)\s+table\s+(\d+\.?\d*)", "table"),
            (r"(?i)(?:see|refer to|as shown in)\s+section\s+(\d+\.?\d*)", "section"),
            (r"(?i)(?:see|refer to|as shown in)\s+appendix\s+([A-Za-z]+)", "appendix"),
            (r"(?i)(?:see|refer to|as shown in)\s+figure\s+(\d+\.?\d*)", "figure"),
            (r"(?i)(?:see|refer to|as shown in)\s+schedule\s+(\d+\.?\d*)", "schedule"),
        ]
    
    def get_chunker_type(self) -> str:
        return "cross_reference_preserving"
    
    def chunk_document(self, document: Document) -> List[Document]:
        """Chunk document while resolving cross-references"""
        content = document.page_content
        metadata = document.metadata
        
        # First pass: identify all references and targets
        references = self._extract_references(content)
        targets = self._extract_targets(content)
        
        # Create reference map
        reference_map = self._create_reference_map(references, targets)
        
        # Standard chunking first
        base_chunks = self.base_splitter.split_documents([document])
        
        # Enhance chunks with cross-reference resolution
        enhanced_chunks = []
        
        for i, chunk in enumerate(base_chunks):
            enhanced_chunk = self._enhance_chunk_with_references(
                chunk, reference_map, content, i, len(base_chunks)
            )
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _extract_references(self, content: str) -> List[Dict[str, Any]]:
        """Extract all cross-references from content"""
        references = []
        
        for pattern, ref_type in self.reference_patterns:
            matches = re.finditer(pattern, content)
            
            for match in matches:
                references.append({
                    "text": match.group(0),
                    "type": ref_type,
                    "target_id": match.group(1),
                    "position": match.start(),
                    "end_position": match.end()
                })
        
        return references
    
    def _extract_targets(self, content: str) -> List[Dict[str, Any]]:
        """Extract reference targets (tables, sections, etc.)"""
        targets = []
        
        # Target patterns
        target_patterns = [
            (r"(?i)table\s+(\d+\.?\d*)[:\s]+(.{0,100})", "table"),
            (r"(?i)section\s+(\d+\.?\d*)[:\s]+(.{0,100})", "section"),
            (r"(?i)appendix\s+([A-Za-z]+)[:\s]+(.{0,100})", "appendix"),
            (r"(?i)figure\s+(\d+\.?\d*)[:\s]+(.{0,100})", "figure"),
            (r"(?i)schedule\s+(\d+\.?\d*)[:\s]+(.{0,100})", "schedule"),
        ]
        
        for pattern, target_type in target_patterns:
            matches = re.finditer(pattern, content)
            
            for match in matches:
                target_content = self._extract_target_content(
                    content, match.start(), target_type
                )
                
                targets.append({
                    "id": match.group(1),
                    "type": target_type,
                    "title": match.group(2).strip() if len(match.groups()) > 1 else "",
                    "position": match.start(),
                    "content": target_content
                })
        
        return targets
    
    def _extract_target_content(
        self, 
        content: str, 
        position: int, 
        target_type: str
    ) -> str:
        """Extract the full content of a reference target"""
        # Define content boundaries based on target type
        if target_type == "table":
            # For tables, find the end of the table structure
            start = position
            end = position + 2000  # Max table size
            
            # Look for table boundaries
            text_after = content[position:end]
            
            # Find end of table (double newline or new section)
            table_end_match = re.search(r'\n\n(?=[A-Z])', text_after)
            if table_end_match:
                end = position + table_end_match.start()
            
            return content[start:end]
        
        else:
            # For sections, get a reasonable chunk
            start = max(0, position - 100)
            end = min(len(content), position + 1000)
            return content[start:end]
    
    def _create_reference_map(
        self, 
        references: List[Dict[str, Any]], 
        targets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Create a mapping between references and their targets"""
        reference_map = {}
        
        # Create lookup for targets
        target_lookup = {}
        for target in targets:
            key = f"{target['type']}_{target['id']}"
            target_lookup[key] = target
        
        # Map references to targets
        for ref in references:
            key = f"{ref['type']}_{ref['target_id']}"
            if key in target_lookup:
                reference_map[ref['text']] = {
                    "reference": ref,
                    "target": target_lookup[key]
                }
        
        return reference_map
    
    def _enhance_chunk_with_references(
        self, 
        chunk: Document, 
        reference_map: Dict[str, Dict[str, Any]], 
        full_content: str,
        chunk_index: int,
        total_chunks: int
    ) -> Document:
        """Enhance chunk with resolved cross-references"""
        content = chunk.page_content
        enhanced_content = content
        chunk_references = []
        
        # Find references in this chunk
        for ref_text, ref_info in reference_map.items():
            if ref_text in content:
                chunk_references.append(ref_info)
                
                # Add resolved reference context
                target_info = ref_info["target"]
                reference_context = f"\n\n[REFERENCE CONTEXT: {ref_text}]\n"
                reference_context += f"{target_info['type'].title()} {target_info['id']}: {target_info['title']}\n"
                reference_context += f"Content: {target_info['content'][:300]}...\n"
                reference_context += "[END REFERENCE CONTEXT]\n"
                
                enhanced_content += reference_context
        
        # Update metadata
        enhanced_metadata = {
            **chunk.metadata,
            "chunk_type": "cross_reference_enhanced",
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "has_cross_references": len(chunk_references) > 0,
            "cross_references_count": len(chunk_references),
            "cross_references": [
                {
                    "reference_text": ref["reference"]["text"],
                    "target_type": ref["target"]["type"],
                    "target_id": ref["target"]["id"],
                    "target_title": ref["target"]["title"]
                }
                for ref in chunk_references
            ],
            "chunker_type": self.get_chunker_type()
        }
        
        return Document(
            page_content=enhanced_content,
            metadata=enhanced_metadata
        )

class SemanticBankingChunker(BankingChunker):
    """
    Semantic chunker that maintains topic coherence
    Solves: Inconsistent Responses challenge
    """
    
    def __init__(
        self,
        embedding_model: Optional[str] = None,
        breakpoint_threshold: float = 0.5,
        max_chunk_size: int = 2000,
        min_chunk_size: int = 100
    ):
        self.embedding_model = embedding_model or settings.openai_embedding_model
        self.breakpoint_threshold = breakpoint_threshold
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        
        try:
            embeddings = OpenAIEmbeddings(
                model=self.embedding_model,
                api_key=settings.openai_api_key
            )
            
            self.semantic_splitter = SemanticChunker(
                embeddings=embeddings,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=int(breakpoint_threshold * 100)
            )
        except Exception as e:
            logger.warning(f"Failed to initialize semantic chunker: {e}")
            # Fallback to recursive splitter
            self.semantic_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
    
    def get_chunker_type(self) -> str:
        return "semantic_banking"
    
    def chunk_document(self, document: Document) -> List[Document]:
        """Chunk document using semantic similarity"""
        try:
            chunks = self.semantic_splitter.split_documents([document])
        except Exception as e:
            logger.warning(f"Semantic chunking failed, using fallback: {e}")
            # Fallback to recursive chunking
            fallback_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = fallback_splitter.split_documents([document])
        
        # Post-process chunks for banking-specific enhancements
        enhanced_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Identify chunk topic/theme
            topic = self._identify_banking_topic(chunk.page_content)
            
            # Check for compliance relevance
            is_compliance = self._is_compliance_relevant(chunk.page_content)
            
            # Enhanced metadata
            enhanced_metadata = {
                **chunk.metadata,
                "chunk_type": "semantic",
                "chunk_index": i,
                "total_chunks": len(chunks),
                "semantic_topic": topic,
                "compliance_relevant": is_compliance,
                "chunk_size": len(chunk.page_content),
                "chunker_type": self.get_chunker_type()
            }
            
            enhanced_chunk = Document(
                page_content=chunk.page_content,
                metadata=enhanced_metadata
            )
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _identify_banking_topic(self, content: str) -> str:
        """Identify the main banking topic of the content"""
        content_lower = content.lower()
        
        # Banking topic keywords
        topics = {
            "loan_products": ["loan", "mortgage", "credit", "lending", "borrowing"],
            "interest_rates": ["rate", "apr", "interest", "yield", "return"],
            "compliance": ["compliance", "regulation", "regulatory", "requirement", "rule"],
            "risk_management": ["risk", "assessment", "evaluation", "mitigation"],
            "customer_service": ["customer", "service", "support", "assistance"],
            "payment_processing": ["payment", "transaction", "processing", "settlement"],
            "account_management": ["account", "balance", "statement", "deposit"],
            "investment": ["investment", "portfolio", "asset", "fund", "equity"],
            "insurance": ["insurance", "policy", "coverage", "premium", "claim"],
            "general": []
        }
        
        topic_scores = {}
        for topic, keywords in topics.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        return "general"
    
    def _is_compliance_relevant(self, content: str) -> bool:
        """Check if content is relevant to compliance"""
        compliance_keywords = [
            "regulation", "regulatory", "compliance", "requirement", "mandate",
            "policy", "procedure", "guideline", "rule", "law", "legal",
            "audit", "review", "oversight", "supervision", "enforcement"
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in compliance_keywords)

class HybridBankingChunker(BankingChunker):
    """
    Hybrid chunker that combines multiple strategies
    Provides the best of all approaches
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        use_table_preservation: bool = True,
        use_cross_reference_resolution: bool = True,
        use_semantic_chunking: bool = True
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_table_preservation = use_table_preservation
        self.use_cross_reference_resolution = use_cross_reference_resolution
        self.use_semantic_chunking = use_semantic_chunking
        
        # Initialize sub-chunkers
        self.table_chunker = TablePreservingChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.reference_chunker = CrossReferenceChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        if use_semantic_chunking:
            self.semantic_chunker = SemanticBankingChunker()
    
    def get_chunker_type(self) -> str:
        return "hybrid_banking"
    
    def chunk_document(self, document: Document) -> List[Document]:
        """Apply hybrid chunking strategy"""
        # Start with base document
        current_doc = document
        
        # Apply table preservation if needed
        if self.use_table_preservation and self._has_tables(document.page_content):
            table_chunks = self.table_chunker.chunk_document(current_doc)
            if len(table_chunks) == 1:
                current_doc = table_chunks[0]
            else:
                # Multiple chunks from table processing
                final_chunks = []
                for chunk in table_chunks:
                    processed_chunk = self._apply_remaining_strategies(chunk)
                    final_chunks.extend(processed_chunk)
                return final_chunks
        
        # Apply remaining strategies to single document
        return self._apply_remaining_strategies(current_doc)
    
    def _has_tables(self, content: str) -> bool:
        """Check if content contains tables"""
        table_indicators = [
            r"\|.*\|.*\|",  # Pipe tables
            r"(?i)table\s+\d+",  # Table references
            r"(?i)rate\s+sheet",  # Rate sheets
            r"^\s*\w+\s+\w+\s+\w+\s*$"  # Multi-column layout
        ]
        
        for pattern in table_indicators:
            if re.search(pattern, content, re.MULTILINE):
                return True
        return False
    
    def _apply_remaining_strategies(self, document: Document) -> List[Document]:
        """Apply cross-reference and semantic chunking"""
        current_chunks = [document]
        
        # Apply cross-reference resolution
        if self.use_cross_reference_resolution:
            enhanced_chunks = []
            for chunk in current_chunks:
                ref_chunks = self.reference_chunker.chunk_document(chunk)
                enhanced_chunks.extend(ref_chunks)
            current_chunks = enhanced_chunks
        
        # Apply semantic chunking if document is large
        if (self.use_semantic_chunking and 
            any(len(chunk.page_content) > self.chunk_size * 1.5 for chunk in current_chunks)):
            
            final_chunks = []
            for chunk in current_chunks:
                if len(chunk.page_content) > self.chunk_size * 1.5:
                    semantic_chunks = self.semantic_chunker.chunk_document(chunk)
                    final_chunks.extend(semantic_chunks)
                else:
                    # Update metadata to indicate hybrid processing
                    chunk.metadata.update({
                        "chunker_type": self.get_chunker_type(),
                        "hybrid_processed": True
                    })
                    final_chunks.append(chunk)
            current_chunks = final_chunks
        
        # Final metadata update
        for i, chunk in enumerate(current_chunks):
            chunk.metadata.update({
                "chunk_index": i,
                "total_chunks": len(current_chunks),
                "chunker_type": self.get_chunker_type()
            })
        
        return current_chunks

# Factory function for easy chunker selection
def get_banking_chunker(
    chunker_type: str = "hybrid",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> BankingChunker:
    """Factory function to get the appropriate chunker"""
    
    chunker_map = {
        "table_preserving": TablePreservingChunker,
        "cross_reference": CrossReferenceChunker,
        "semantic": SemanticBankingChunker,
        "hybrid": HybridBankingChunker
    }
    
    if chunker_type not in chunker_map:
        raise ValueError(f"Unknown chunker type: {chunker_type}")
    
    chunker_class = chunker_map[chunker_type]
    
    # Pass appropriate parameters to each chunker
    if chunker_type == "semantic":
        return chunker_class(**kwargs)
    else:
        return chunker_class(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs
        )

# Example usage and testing
if __name__ == "__main__":
    from pathlib import Path
    from src.document_loaders import load_banking_documents
    
    # Load test documents
    docs_path = Path(__file__).parent.parent / "Documents"
    if docs_path.exists():
        documents = load_banking_documents(str(docs_path))
        
        if documents:
            print(f"Testing chunking strategies with {len(documents)} documents")
            
            # Test different chunkers
            chunkers = [
                ("Table Preserving", get_banking_chunker("table_preserving")),
                ("Cross-Reference", get_banking_chunker("cross_reference")),
                ("Semantic", get_banking_chunker("semantic")),
                ("Hybrid", get_banking_chunker("hybrid"))
            ]
            
            for name, chunker in chunkers:
                try:
                    chunks = chunker.chunk_document(documents[0])
                    print(f"\n{name} Chunker: Created {len(chunks)} chunks")
                    print(f"First chunk preview: {chunks[0].page_content[:100]}...")
                    print(f"Chunk metadata: {list(chunks[0].metadata.keys())}")
                except Exception as e:
                    print(f"{name} Chunker failed: {e}")
        else:
            print("No documents found for testing")
    else:
        print(f"Documents directory not found: {docs_path}") 