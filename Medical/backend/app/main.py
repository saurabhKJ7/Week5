from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import fitz
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
import os
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Medical Knowledge Assistant")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize metrics
QUERY_PROCESSING_TIME = Histogram('query_processing_seconds', 'Time spent processing query')
UPLOAD_PROCESSING_TIME = Histogram('upload_processing_seconds', 'Time spent processing upload')
QUERY_COUNTER = Counter('queries_total', 'Total number of queries processed')
UPLOAD_COUNTER = Counter('uploads_total', 'Total number of documents uploaded')

# Initialize OpenAI components
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(temperature=0, model="gpt-4")  # Using GPT-4 for better comprehension

# Initialize text splitter with larger chunk size and overlap
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,  # Increased from 1000
    chunk_overlap=400,  # Increased from 200
    separators=["\n\n", "\n", " ", ""]  # Added more separators for better splitting
)

# Initialize FAISS vector store
vector_store = None

class Query(BaseModel):
    question: str

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global vector_store
    try:
        start_time = time.time()
        logger.info(f"Processing upload for file: {file.filename}")
        
        # Save the uploaded file temporarily
        temp_path = f"data/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process PDF file
        doc = fitz.open(temp_path)
        text = ""
        for page in doc:
            text += page.get_text()
        
        # Split text into chunks
        chunks = text_splitter.split_text(text)
        
        # Create or update vector store
        vector_store = FAISS.from_texts(chunks, embeddings)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        UPLOAD_COUNTER.inc()
        UPLOAD_PROCESSING_TIME.observe(time.time() - start_time)
        
        return {"message": "File processed successfully"}
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def process_query(query: Query):
    if not vector_store:
        raise HTTPException(status_code=400, detail="No documents have been uploaded yet")
    
    try:
        start_time = time.time()
        logger.info(f"Processing query: {query.question}")
        
        # Retrieve more relevant documents
        docs = vector_store.similarity_search(query.question, k=6)  # Increased from 4
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Create prompt template with more specific instructions
        prompt = ChatPromptTemplate.from_template("""You are a medical knowledge assistant. Your task is to provide comprehensive and detailed answers based on the provided context. Focus on accuracy, completeness, and clarity.

Context: {context}

Question: {question}

Please provide a detailed answer that:
1. Covers all relevant aspects from the context
2. Explains any medical or legal implications
3. Includes specific examples or scenarios if available
4. Maintains a professional and clear tone
5. Organizes information in a logical structure

If you cannot answer the question based on the context, say "I cannot answer this question based on the provided context."

Answer: """)
        
        # Create chain
        chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt
            | llm
        )
        
        # Get response
        response = chain.invoke({"context": context, "question": query.question})
        
        QUERY_COUNTER.inc()
        QUERY_PROCESSING_TIME.observe(time.time() - start_time)
        
        return {
            "answer": response.content,
            "context": context
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST) 