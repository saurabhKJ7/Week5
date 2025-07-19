"""
Banking RAG System - Main FastAPI Application
Comprehensive AI assistant for banking knowledge base using LangChain
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from src.config import get_settings
from src.document_loaders import load_banking_documents
from src.chunking_strategies import get_banking_chunker
from src.vectorstore import get_banking_vector_store, BankingVectorStore
from src.retrieval_chains import create_banking_rag_pipeline, BankingRAGPipeline
from src.banking_workflows import create_banking_workflow_orchestrator, BankingWorkflowOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Banking RAG System",
    description="AI-powered banking knowledge base using LangChain and Supabase",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for system components
vector_store: Optional[BankingVectorStore] = None
rag_pipeline: Optional[BankingRAGPipeline] = None
workflow_orchestrator: Optional[BankingWorkflowOrchestrator] = None
system_stats = {
    "startup_time": datetime.now().isoformat(),
    "documents_processed": 0,
    "total_queries": 0,
    "system_ready": False
}

# Pydantic Models for API

class QueryRequest(BaseModel):
    """Query request model"""
    question: str = Field(..., description="Question to ask the banking AI")
    use_conversation: bool = Field(default=False, description="Use conversational mode")
    include_sources: bool = Field(default=True, description="Include source documents")
    
class QueryResponse(BaseModel):
    """Query response model"""
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    confidence: str
    pipeline_type: str
    timestamp: str

class WorkflowRequest(BaseModel):
    """Specialized workflow request model"""
    workflow_type: str = Field(..., description="Type of workflow: rate_inquiry, compliance_analysis, underwriting_evaluation, policy_guidance")
    parameters: Dict[str, Any] = Field(..., description="Workflow-specific parameters")

class DocumentUploadRequest(BaseModel):
    """Document upload request model"""
    file_path: str = Field(..., description="Path to document file")
    document_type: Optional[str] = None
    chunking_strategy: str = Field(default="hybrid", description="Chunking strategy to use")

class SystemStatus(BaseModel):
    """System status model"""
    system_ready: bool
    vector_store_ready: bool
    documents_in_store: int
    startup_time: str
    uptime_seconds: float

# Dependency to get vector store
async def get_vector_store() -> BankingVectorStore:
    """Dependency to get vector store instance"""
    global vector_store
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    return vector_store

# Dependency to get RAG pipeline
async def get_rag_pipeline() -> BankingRAGPipeline:
    """Dependency to get RAG pipeline instance"""
    global rag_pipeline
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    return rag_pipeline

# Dependency to get workflow orchestrator
async def get_workflow_orchestrator() -> BankingWorkflowOrchestrator:
    """Dependency to get workflow orchestrator instance"""
    global workflow_orchestrator
    if workflow_orchestrator is None:
        raise HTTPException(status_code=503, detail="Workflow orchestrator not initialized")
    return workflow_orchestrator

@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup"""
    global vector_store, rag_pipeline, workflow_orchestrator, system_stats
    
    try:
        logger.info("Starting Banking RAG System...")
        
        # Validate configuration
        try:
            settings.validate_required_settings()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            logger.error("Please check your environment variables in .env file")
            return
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = get_banking_vector_store()
        
        # Setup database schema
        await vector_store.setup_database_schema()
        logger.info("Database schema setup completed")
        
        # Initialize RAG pipeline
        logger.info("Initializing RAG pipeline...")
        rag_pipeline = create_banking_rag_pipeline(vector_store)
        
        # Initialize workflow orchestrator
        logger.info("Initializing workflow orchestrator...")
        workflow_orchestrator = create_banking_workflow_orchestrator(vector_store)
        
        # Load initial documents if available
        documents_path = Path("Documents")
        if documents_path.exists():
            logger.info("Loading initial documents...")
            await load_initial_documents()
        
        system_stats["system_ready"] = True
        logger.info("Banking RAG System startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        system_stats["startup_error"] = str(e)

async def load_initial_documents():
    """Load initial documents from the Documents directory"""
    global system_stats
    
    try:
        documents_path = Path("Documents")
        if not documents_path.exists():
            logger.info("No Documents directory found, skipping initial document loading")
            return
        
        # Load documents
        logger.info("Loading banking documents...")
        documents = load_banking_documents(str(documents_path))
        
        if not documents:
            logger.info("No documents found to load")
            return
        
        logger.info(f"Loaded {len(documents)} documents")
        
        # Chunk documents
        logger.info("Chunking documents...")
        chunker = get_banking_chunker("hybrid")
        all_chunks = []
        
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks")
        
        # Add to vector store
        if all_chunks:
            logger.info("Adding documents to vector store...")
            await asyncio.get_event_loop().run_in_executor(
                None, vector_store.add_documents, all_chunks
            )
            
            system_stats["documents_processed"] = len(all_chunks)
            logger.info(f"Successfully added {len(all_chunks)} document chunks to vector store")
        
    except Exception as e:
        logger.error(f"Error loading initial documents: {e}")

# API Routes

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "service": "Banking RAG System",
        "version": "1.0.0",
        "description": "AI-powered banking knowledge base using LangChain",
        "status": "ready" if system_stats["system_ready"] else "initializing",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - datetime.fromisoformat(system_stats["startup_time"])).total_seconds()
    
    return SystemStatus(
        system_ready=system_stats["system_ready"],
        vector_store_ready=vector_store is not None,
        documents_in_store=system_stats["documents_processed"],
        startup_time=system_stats["startup_time"],
        uptime_seconds=uptime
    )

@app.post("/query", response_model=QueryResponse)
async def query_banking_ai(
    request: QueryRequest,
    pipeline: BankingRAGPipeline = Depends(get_rag_pipeline)
):
    """Ask a question to the banking AI"""
    
    try:
        system_stats["total_queries"] += 1
        
        # Process the query
        result = pipeline.ask_question(
            request.question, 
            use_conversation=request.use_conversation
        )
        
        # Format response
        response = QueryResponse(
            answer=result["answer"],
            sources=result.get("source_documents", []) if request.include_sources else None,
            confidence=result.get("confidence", "medium"),
            pipeline_type=result.get("pipeline_type", "unknown"),
            timestamp=datetime.now().isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/workflow")
async def execute_specialized_workflow(
    request: WorkflowRequest,
    orchestrator: BankingWorkflowOrchestrator = Depends(get_workflow_orchestrator)
):
    """Execute a specialized banking workflow"""
    
    try:
        # Route request to appropriate workflow
        result = orchestrator.route_request(
            request.workflow_type,
            **request.parameters
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@app.post("/documents/upload")
async def upload_document(
    request: DocumentUploadRequest,
    background_tasks: BackgroundTasks,
    vs: BankingVectorStore = Depends(get_vector_store)
):
    """Upload and process a new document"""
    
    try:
        # Validate file path
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Add background task to process document
        background_tasks.add_task(
            process_document_background,
            str(file_path),
            request.document_type,
            request.chunking_strategy
        )
        
        return {
            "message": "Document upload initiated",
            "file_path": str(file_path),
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

async def process_document_background(
    file_path: str, 
    document_type: Optional[str], 
    chunking_strategy: str
):
    """Background task to process uploaded document"""
    
    try:
        logger.info(f"Processing document: {file_path}")
        
        # Load document
        documents = load_banking_documents(file_path)
        
        if not documents:
            logger.error(f"No content extracted from document: {file_path}")
            return
        
        # Update metadata if document type provided
        if document_type:
            for doc in documents:
                doc.metadata["document_type"] = document_type
        
        # Chunk document
        chunker = get_banking_chunker(chunking_strategy)
        all_chunks = []
        
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
        
        # Add to vector store
        if all_chunks:
            vector_store.add_documents(all_chunks)
            system_stats["documents_processed"] += len(all_chunks)
            logger.info(f"Successfully processed document: {file_path} ({len(all_chunks)} chunks)")
        
    except Exception as e:
        logger.error(f"Background document processing error: {e}")

@app.get("/documents/stats")
async def get_document_stats(vs: BankingVectorStore = Depends(get_vector_store)):
    """Get document collection statistics"""
    
    try:
        stats = vs.get_collection_stats()
        return {
            **stats,
            "processed_documents": system_stats["documents_processed"],
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/search/hybrid")
async def hybrid_search(
    query: str = Query(..., description="Search query"),
    k: int = Query(default=5, description="Number of results to return"),
    vs: BankingVectorStore = Depends(get_vector_store)
):
    """Perform hybrid search on the document collection"""
    
    try:
        results = vs.hybrid_search(query, k=k)
        
        formatted_results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in results
        ]
        
        return {
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search/compliance")
async def compliance_search(
    query: str = Query(..., description="Compliance search query"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    k: int = Query(default=5, description="Number of results to return"),
    vs: BankingVectorStore = Depends(get_vector_store)
):
    """Search compliance-relevant documents"""
    
    try:
        results = vs.search_compliance(query, risk_level=risk_level, k=k)
        
        formatted_results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in results
        ]
        
        return {
            "query": query,
            "risk_level_filter": risk_level,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Compliance search error: {e}")
        raise HTTPException(status_code=500, detail=f"Compliance search failed: {str(e)}")

@app.get("/search/tables")
async def table_search(
    query: str = Query(..., description="Table search query"),
    table_type: Optional[str] = Query(None, description="Filter by table type"),
    k: int = Query(default=5, description="Number of results to return"),
    vs: BankingVectorStore = Depends(get_vector_store)
):
    """Search table-containing documents"""
    
    try:
        results = vs.search_tables(query, table_type=table_type, k=k)
        
        formatted_results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in results
        ]
        
        return {
            "query": query,
            "table_type_filter": table_type,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Table search error: {e}")
        raise HTTPException(status_code=500, detail=f"Table search failed: {str(e)}")

@app.get("/system/stats")
async def get_system_stats(
    pipeline: BankingRAGPipeline = Depends(get_rag_pipeline),
    orchestrator: BankingWorkflowOrchestrator = Depends(get_workflow_orchestrator)
):
    """Get comprehensive system statistics"""
    
    try:
        uptime = (datetime.now() - datetime.fromisoformat(system_stats["startup_time"])).total_seconds()
        
        return {
            "system": {
                **system_stats,
                "uptime_seconds": uptime,
                "current_time": datetime.now().isoformat()
            },
            "pipeline": pipeline.get_stats(),
            "workflows": orchestrator.get_usage_stats()
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="info"
    ) 