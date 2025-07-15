from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import SessionLocal
from ...db import models
from ...utils.file_parser import extract_text
from ...utils.chunking import chunk_text_by_sentence
import shutil
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No file name provided")
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_doc = models.Document(filename=file.filename, content_type=file.content_type, extra_data={"path": file_path})
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return {"filename": file.filename, "content_type": file.content_type, "id": new_doc.id}

@router.post("/{doc_id}/process")
def process_document(doc_id: uuid.UUID, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.processed is True:
        return {"message": "Document already processed"}

    file_path = str(doc.extra_data.get("path"))
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document file not found")

    text = extract_text(file_path, str(doc.content_type))
    chunks = chunk_text_by_sentence(text)

    for i, chunk_text in enumerate(chunks):
        new_chunk = models.Chunk(
            document_id=doc.id,
            content=chunk_text,
            chunk_index=i
        )
        db.add(new_chunk)
    
    setattr(doc, 'processed', True)
    db.commit()

    return {"message": f"Document processed into {len(chunks)} chunks."} 

@router.get("/")
def get_documents(processed: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Document)
    if processed is not None:
        query = query.filter(models.Document.processed == processed)
    
    docs = query.all()
    return docs 