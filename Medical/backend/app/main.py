from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import fitz
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
import os
import re
import json
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
BLOCKED_ANSWERS = Counter('blocked_answers_total', 'Total number of blocked unsafe answers')
SAFETY_VIOLATIONS = Counter('safety_violations_total', 'Total number of safety violations', ['violation_type'])
HALLUCINATION_DETECTIONS = Counter('hallucination_detections_total', 'Total number of hallucination detections')

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

# Safety configuration
SAFETY_THRESHOLDS = {
    "min_faithfulness": 0.90,
    "min_context_precision": 0.85,
    "min_answer_relevance": 0.80
}

# Experimental/unapproved drugs list
EXPERIMENTAL_DRUGS = [
    "thalidomide", "thalomid", "experimental", "investigational", "unapproved",
    "phase i", "phase ii", "phase iii", "clinical trial", "off-label",
    "compassionate use", "expanded access", "emergency use"
]

# Dosage patterns that require context
DOSAGE_PATTERNS = [
    r'\d+\s*(mg|g|ml|mcg|units?)\s*(per|/)\s*(day|dose|hour|hr)',
    r'\d+\s*(mg|g|ml|mcg|units?)\s*(twice|three times|four times)\s*(daily|per day)',
    r'\d+\s*(mg|g|ml|mcg|units?)\s*(q\d+|every\s+\d+)',
    r'start with\s+\d+',
    r'increase to\s+\d+',
    r'maximum\s+\d+',
    r'initial dose\s+\d+',
    r'maintenance dose\s+\d+'
]

class Query(BaseModel):
    question: str

class SafetyResult(BaseModel):
    is_safe: bool
    violations: List[str]
    metrics: Dict[str, float]
    confidence_score: float

def calculate_faithfulness_score(answer: str, context: str) -> float:
    """Calculate faithfulness score based on answer-context alignment."""
    answer_lower = answer.lower()
    context_lower = context.lower()
    
    # Check for key medical terms in both answer and context
    medical_terms = re.findall(r'\b(?:drug|medication|dose|dosage|side effect|contraindication|indication|treatment|therapy|patient|clinical|medical|disease|condition|symptom|diagnosis|prognosis)\b', answer_lower)
    context_terms = re.findall(r'\b(?:drug|medication|dose|dosage|side effect|contraindication|indication|treatment|therapy|patient|clinical|medical|disease|condition|symptom|diagnosis|prognosis)\b', context_lower)
    
    if not medical_terms:
        return 0.5  # Neutral score if no medical terms
    
    # Calculate overlap
    overlap = len(set(medical_terms) & set(context_terms))
    total_terms = len(set(medical_terms) | set(context_terms))
    
    if total_terms == 0:
        return 0.5
    
    return overlap / total_terms

def calculate_context_precision(answer: str, context: str, question: str) -> float:
    """Calculate context precision score."""
    # Check if answer directly references context information
    context_sentences = context.split('.')
    answer_sentences = answer.split('.')
    
    relevant_sentences = 0
    for ans_sent in answer_sentences:
        for ctx_sent in context_sentences:
            if any(word in ctx_sent.lower() for word in ans_sent.lower().split() if len(word) > 3):
                relevant_sentences += 1
                break
    
    if not answer_sentences:
        return 0.0
    
    return min(relevant_sentences / len(answer_sentences), 1.0)

def calculate_answer_relevance(answer: str, question: str) -> float:
    """Calculate answer relevance to the question."""
    question_words = set(question.lower().split())
    answer_words = set(answer.lower().split())
    
    if not question_words:
        return 0.0
    
    overlap = len(question_words & answer_words)
    return min(overlap / len(question_words), 1.0)

def detect_hallucinations(answer: str, context: str) -> List[str]:
    """Detect potential hallucinations in the answer."""
    hallucinations = []
    
    # Check for specific claims not in context
    answer_lower = answer.lower()
    context_lower = context.lower()
    
    # Look for specific numbers/statistics not in context
    numbers_in_answer = re.findall(r'\b\d+(?:\.\d+)?%?\b', answer)
    numbers_in_context = re.findall(r'\b\d+(?:\.\d+)?%?\b', context)
    
    for num in numbers_in_answer:
        if num not in numbers_in_context and len(num) > 2:  # Ignore single digits
            hallucinations.append(f"Specific number {num} not found in context")
    
    # Check for drug names not in context
    drug_mentions = re.findall(r'\b[A-Z][a-z]+(?:mycin|cin|zole|pam|pine|sine|pril|sartan|olol|pine|zine)\b', answer)
    for drug in drug_mentions:
        if drug.lower() not in context_lower:
            hallucinations.append(f"Drug {drug} not mentioned in context")
    
    # Check for specific medical claims not supported by context
    medical_claims = re.findall(r'\b(?:causes|caused by|leads to|results in|associated with)\b', answer_lower)
    for claim in medical_claims:
        if claim not in context_lower:
            hallucinations.append(f"Causal claim '{claim}' not supported by context")
    
    return hallucinations

def validate_dosage_safety(answer: str, context: str) -> List[str]:
    """Validate dosage information safety."""
    violations = []
    answer_lower = answer.lower()
    
    # Check for dosage patterns
    dosage_matches = []
    for pattern in DOSAGE_PATTERNS:
        matches = re.findall(pattern, answer_lower)
        dosage_matches.extend(matches)
    
    if dosage_matches:
        # Check if context contains dosage information
        context_has_dosage = any(re.search(pattern, context.lower()) for pattern in DOSAGE_PATTERNS)
        if not context_has_dosage:
            violations.append("Dosage information provided without proper context")
    
    return violations

def check_experimental_drugs(answer: str) -> List[str]:
    """Check for mentions of experimental or unapproved drugs."""
    violations = []
    answer_lower = answer.lower()
    
    for drug in EXPERIMENTAL_DRUGS:
        if drug in answer_lower:
            violations.append(f"Experimental/unapproved drug mentioned: {drug}")
    
    return violations

def perform_safety_checks(answer: str, context: str, question: str) -> SafetyResult:
    """Perform comprehensive safety checks on the answer."""
    violations = []
    
    # Calculate metrics
    faithfulness = calculate_faithfulness_score(answer, context)
    context_precision = calculate_context_precision(answer, context, question)
    answer_relevance = calculate_answer_relevance(answer, question)
    
    # Check thresholds
    if faithfulness < SAFETY_THRESHOLDS["min_faithfulness"]:
        violations.append(f"Low faithfulness score: {faithfulness:.2f} < {SAFETY_THRESHOLDS['min_faithfulness']}")
        SAFETY_VIOLATIONS.labels(violation_type="low_faithfulness").inc()
    
    if context_precision < SAFETY_THRESHOLDS["min_context_precision"]:
        violations.append(f"Low context precision: {context_precision:.2f} < {SAFETY_THRESHOLDS['min_context_precision']}")
        SAFETY_VIOLATIONS.labels(violation_type="low_context_precision").inc()
    
    if answer_relevance < SAFETY_THRESHOLDS["min_answer_relevance"]:
        violations.append(f"Low answer relevance: {answer_relevance:.2f} < {SAFETY_THRESHOLDS['min_answer_relevance']}")
        SAFETY_VIOLATIONS.labels(violation_type="low_answer_relevance").inc()
    
    # Check for experimental drugs
    experimental_violations = check_experimental_drugs(answer)
    violations.extend(experimental_violations)
    if experimental_violations:
        SAFETY_VIOLATIONS.labels(violation_type="experimental_drugs").inc()
    
    # Check dosage safety
    dosage_violations = validate_dosage_safety(answer, context)
    violations.extend(dosage_violations)
    if dosage_violations:
        SAFETY_VIOLATIONS.labels(violation_type="unsafe_dosage").inc()
    
    # Check for hallucinations
    hallucinations = detect_hallucinations(answer, context)
    violations.extend(hallucinations)
    if hallucinations:
        HALLUCINATION_DETECTIONS.inc()
        SAFETY_VIOLATIONS.labels(violation_type="hallucination").inc()
    
    # Calculate confidence score
    confidence = (faithfulness + context_precision + answer_relevance) / 3
    
    is_safe = len(violations) == 0
    
    return SafetyResult(
        is_safe=is_safe,
        violations=violations,
        metrics={
            "faithfulness": faithfulness,
            "context_precision": context_precision,
            "answer_relevance": answer_relevance
        },
        confidence_score=confidence
    )

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
        
        # Create prompt template with safety instructions
        prompt = ChatPromptTemplate.from_template("""You are a medical knowledge assistant. Your task is to provide comprehensive and detailed answers based on the provided context. Focus on accuracy, completeness, and clarity.

IMPORTANT SAFETY GUIDELINES:
- Only provide information that is explicitly supported by the context
- Do not mention experimental or unapproved drugs
- Always provide proper context for any dosage information
- If uncertain, clearly state the limitations
- Never provide specific medical advice without proper context

Context: {context}

Question: {question}

Please provide a detailed answer that:
1. Covers all relevant aspects from the context
2. Explains any medical or legal implications
3. Includes specific examples or scenarios if available
4. Maintains a professional and clear tone
5. Organizes information in a logical structure
6. Clearly states when information is not available in the context

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
        
        # Perform safety checks
        safety_result = perform_safety_checks(response.content, context, query.question)
        
        # Block unsafe responses
        if not safety_result.is_safe:
            BLOCKED_ANSWERS.inc()
            logger.warning(f"Blocked unsafe response: {safety_result.violations}")
            return {
                "answer": "I cannot provide a safe answer to this question based on the available information. Please consult with a qualified healthcare professional.",
                "context": context,
                "safety_result": safety_result.dict(),
                "blocked": True,
                "violations": safety_result.violations
            }
        
        QUERY_COUNTER.inc()
        QUERY_PROCESSING_TIME.observe(time.time() - start_time)
        
        return {
            "answer": response.content,
            "context": context,
            "safety_result": safety_result.dict(),
            "blocked": False
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/safety-stats")
async def get_safety_stats():
    """Get safety statistics for monitoring."""
    return {
        "blocked_answers": BLOCKED_ANSWERS._value.get(),
        "safety_violations": {
            "low_faithfulness": SAFETY_VIOLATIONS.labels(violation_type="low_faithfulness")._value.get(),
            "low_context_precision": SAFETY_VIOLATIONS.labels(violation_type="low_context_precision")._value.get(),
            "low_answer_relevance": SAFETY_VIOLATIONS.labels(violation_type="low_answer_relevance")._value.get(),
            "experimental_drugs": SAFETY_VIOLATIONS.labels(violation_type="experimental_drugs")._value.get(),
            "unsafe_dosage": SAFETY_VIOLATIONS.labels(violation_type="unsafe_dosage")._value.get(),
            "hallucination": SAFETY_VIOLATIONS.labels(violation_type="hallucination")._value.get()
        },
        "hallucination_detections": HALLUCINATION_DETECTIONS._value.get(),
        "safety_thresholds": SAFETY_THRESHOLDS
    } 