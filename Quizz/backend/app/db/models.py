import uuid
from sqlalchemy import Column, String, TIMESTAMP, Boolean, JSON, ForeignKey, Text, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(50))
    upload_date = Column(TIMESTAMP, server_default=func.now())
    processed = Column(Boolean, default=False)
    extra_data = Column(JSON)

    chunks = relationship("Chunk", back_populates="document")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    content = Column(Text)
    # The VECTOR type is not standard in SQLAlchemy, so we'll use JSONB or a similar type for now.
    # In a real application, you might use a pgvector extension for PostgreSQL.
    embedding = Column(JSON) # Placeholder for vector embedding
    chunk_index = Column(Integer)
    extra_data = Column(JSON)

    document = relationship("Document", back_populates="chunks") 