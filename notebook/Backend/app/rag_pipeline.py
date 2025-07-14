from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from typing import List, Dict, Any, Optional, Union
import os
from dotenv import load_dotenv
import logging
from pathlib import Path
from app.document_processor import DocumentProcessor
from app.vision_analyzer import VisionAnalyzer
from pydantic.types import SecretStr
from langchain.docstore.document import Document
from rank_bm25 import BM25Okapi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate environment variables
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

logger.info(f"OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")
logger.info(f"MODEL_NAME: {MODEL_NAME}")
logger.info(f"EMBEDDING_MODEL: {EMBEDDING_MODEL}")

class RAGPipeline:
    def __init__(self) -> None:
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
            
        self.embeddings = OpenAIEmbeddings(api_key=SecretStr(self.openai_api_key))
        self.vector_store = None
        self.document_processor = DocumentProcessor()
        self.vision_analyzer = VisionAnalyzer(api_key=self.openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        
        # For hybrid search
        self.bm25_retriever = None
        self.documents_for_bm25 = []

        try:
            self.llm = ChatOpenAI(
                model=MODEL_NAME,
                temperature=0.7
            )
            logger.info("RAGPipeline initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAGPipeline: {str(e)}")
            raise
    
    def add_document(self, file_path: str):
        logger.info(f"Processing document: {file_path}")
        try:
            content, metadata = self.document_processor.process_file(file_path)
            
            # Handle documents chunked by the processor (e.g., from 'unstructured')
            if "structured_chunks" in metadata and metadata["structured_chunks"]:
                documents = []
                for chunk_meta in metadata["structured_chunks"]:
                    # Each chunk_meta is a dictionary with content and metadata
                    chunk_content = chunk_meta.pop("content", "") # Extract content
                    doc = Document(page_content=chunk_content, metadata=chunk_meta)
                    documents.append(doc)
            else:
                # Fallback for documents not pre-chunked by the processor
                chunks = self.text_splitter.split_text(content)
                documents = [Document(page_content=chunk, metadata={"source": file_path}) for chunk in chunks]

            # Analyze images and add their descriptions as separate documents
            if "images" in metadata and metadata["images"]:
                for image_path in metadata["images"]:
                    prompt = "Describe this image in detail. What objects, text, or concepts are present?"
                    description = self.vision_analyzer.analyze_image(image_path, prompt)
                    image_doc = Document(
                        page_content=f"[Image Description: {description}]",
                        metadata={"source": file_path, "type": "image_analysis"}
                    )
                    documents.append(image_doc)
            
            # Update both Chroma and BM25
            if self.vector_store is None:
                self.vector_store = Chroma.from_documents(documents, self.embeddings)
            else:
                self.vector_store.add_documents(documents)

            self.documents_for_bm25.extend(documents)
            tokenized_corpus = [doc.page_content.split() for doc in self.documents_for_bm25]
            self.bm25_retriever = BM25Okapi(tokenized_corpus)
            
            logger.info(f"Successfully added {len(documents)} chunks from {file_path}")

        except Exception as e:
            logger.error(f"Failed to add document {file_path}. Error: {e}")
            raise

    def hybrid_search(self, query_text: str, k: int = 5) -> List[Document]:
        """
        Performs a hybrid search using both semantic (Chroma) and keyword (BM25) search.
        """
        if self.vector_store is None or self.bm25_retriever is None:
            return []

        # 1. Semantic search with Chroma
        semantic_results = self.vector_store.similarity_search(query_text, k=k)

        # 2. Keyword search with BM25
        tokenized_query = query_text.lower().split()
        bm25_scores = self.bm25_retriever.get_scores(tokenized_query)
        
        # Get top k indices from BM25
        top_k_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:k]
        bm25_results = [self.documents_for_bm25[i] for i in top_k_indices]

        # 3. Combine and de-duplicate results
        combined_results = {doc.page_content: doc for doc in semantic_results}
        for doc in bm25_results:
            if doc.page_content not in combined_results:
                combined_results[doc.page_content] = doc

        return list(combined_results.values())

    def query(self, query_text: str) -> Dict[str, Any]:
        logger.info(f"Executing query: {query_text}")
        if self.vector_store is None:
            raise ValueError("No documents have been added to the pipeline yet.")

        # Use hybrid search to get the most relevant documents
        retrieved_docs = self.hybrid_search(query_text)

        if not retrieved_docs:
            return {"answer": "I couldn't find any relevant documents.", "source_documents": []}

        # Create the context for the language model
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        # Build the prompt
        prompt = f"Based on the following context, please answer the query.\n\nContext:\n{context}\n\nQuery: {query_text}"

        # Get the response from the language model
        response = self.llm.invoke(prompt)

        return {
            "answer": response.content,
            "source_documents": retrieved_docs
        }
    
    def save_vector_store(self, path: Union[str, Path] = "vector_store") -> None:
        """
        Save the vector store to disk
        
        Args:
            path: Path where to save the vector store
        """
        try:
            if self.vector_store:
                path = Path(path)
                path.parent.mkdir(parents=True, exist_ok=True)
                # Chroma persist automatically in directory
                self.vector_store.persist()
                logger.info(f"Vector store saved to {path}")
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            raise
    
    def load_vector_store(self, path: Union[str, Path] = "vector_store") -> None:
        """
        Load the vector store from disk
        
        Args:
            path: Path from where to load the vector store
        
        Raises:
            FileNotFoundError: If the vector store file doesn't exist
        """
        try:
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"Vector store not found at {path}")
                
            self.vector_store = Chroma(persist_directory=str(path), embedding_function=self.embeddings)
            logger.info(f"Chroma vector store loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            raise 