from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from ...db.session import SessionLocal
from ...db import models
from ...services.retrieval import DenseRetriever, SparseRetriever, HybridRetriever
from ...services.reranker import CrossEncoderReranker
from ...services.question_generator import QuestionGenerator
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# In a real application, these would be initialized once and shared.
dense_retriever = DenseRetriever()
sparse_retriever = SparseRetriever()
hybrid_retriever = HybridRetriever(dense_retriever, sparse_retriever)
reranker = CrossEncoderReranker()
question_generator = QuestionGenerator()

@router.post("/generate")
def generate_quiz(
    doc_id: uuid.UUID = Body(...),
    query: str = Body(...),
    num_questions: int = Body(10),
    difficulty: int = Body(2),
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc or not doc.processed:
        raise HTTPException(status_code=404, detail="Document not found or not processed")

    chunks = db.query(models.Chunk).filter(models.Chunk.document_id == doc_id).all()
    if not chunks:
        raise HTTPException(status_code=404, detail="No chunks found for this document")

    chunk_map = {chunk.id: chunk.content for chunk in chunks}
    
    # This is a simplified flow. In a real app, you'd have a more robust way
    # to manage the indexing of documents.
    dense_retriever.encode_documents(list(chunk_map.values()))
    sparse_retriever.add_documents({i: content for i, content in enumerate(list(chunk_map.values()))})
    
    retrieved_chunks = hybrid_retriever.search(query, k=20)
    
    candidate_docs = [chunk["document"] for chunk in retrieved_chunks]
    reranked_docs = reranker.rerank(query, candidate_docs)

    # Use the top 5 reranked documents as context for quiz generation
    context = " ".join(reranked_docs[:5])
    
    quiz = question_generator.generate_quiz(context, difficulty, num_questions)
    
    return {"quiz": quiz} 