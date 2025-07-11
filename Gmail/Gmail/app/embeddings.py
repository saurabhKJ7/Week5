from __future__ import annotations

import json
import os
from typing import List

import faiss
import numpy as np
import openai
from PyPDF2 import PdfReader
from fastapi import HTTPException

from .config import get_settings

settings = get_settings()


def _ensure_dir(file_path: str) -> None:
    """Create directory if it doesn't exist."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def _chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> List[str]:
    """Naive tokenizer-agnostic sliding window chunking."""
    sentences = text.split("\n")
    chunks: List[str] = []
    current: List[str] = []
    length = 0
    for sentence in sentences:
        tokens = sentence.split()
        if length + len(tokens) > max_tokens:
            chunks.append(" ".join(current))
            current = current[-overlap:]
            length = len(current)
        current.extend(tokens)
        length += len(tokens)
    if current:
        chunks.append(" ".join(current))
    return chunks


class DocumentIngestor:
    def __init__(self, index_path: str | None = None):
        """Initialize document ingestor with FAISS index."""
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env"
            )
            
        self.index_path = index_path or settings.vector_db_path
        if not self.index_path:
            raise ValueError("Vector DB path not configured")
            
        self.dim = 1536  # Dimension for OpenAI Ada embeddings
        openai.api_key = settings.openai_api_key
        self._load()

    def _load(self):
        """Load or create FAISS index and metadata."""
        try:
            # Ensure directory exists
            _ensure_dir(self.index_path)
            
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.index_path + ".meta", "r") as f:
                    self.metadata: List[str] = json.load(f)
            else:
                self.index = faiss.IndexFlatL2(self.dim)
                self.metadata = []
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize vector store: {str(e)}"
            )

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        try:
            response = openai.embeddings.create(
                input=texts,
                model="text-embedding-3-small",
            )
            return [d.embedding for d in response.data]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embeddings: {str(e)}"
            )

    def _read_file(self, path: str) -> str:
        """Read and extract text from supported file types."""
        try:
            if path.endswith(".pdf"):
                reader = PdfReader(path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read file {path}: {str(e)}"
            )

    def ingest(self, path: str):
        """Process and index a document."""
        text = self._read_file(path)
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail=f"File {path} appears to be empty"
            )
            
        chunks = _chunk_text(text)
        embeds = self._embed(chunks)
        
        try:
            self.index.add(np.array(embeds, dtype=np.float32))
            self.metadata.extend(chunks)
            self._persist()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to index document: {str(e)}"
            )

    def _persist(self):
        """Save FAISS index and metadata to disk."""
        try:
            _ensure_dir(self.index_path)
            faiss.write_index(self.index, self.index_path)
            with open(self.index_path + ".meta", "w") as f:
                json.dump(self.metadata, f)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save index: {str(e)}"
            )

    def search(self, query: str, k: int = 5) -> List[str]:
        """Search for similar text chunks."""
        try:
            embed = self._embed([query])[0]
            D, I = self.index.search(np.array([embed], dtype=np.float32), k)
            return [self.metadata[i] for i in I[0] if i < len(self.metadata)]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            ) 