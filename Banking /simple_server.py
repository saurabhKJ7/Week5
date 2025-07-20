#!/usr/bin/env python3
"""
Simple test server for Banking RAG System
Works without external API keys for basic functionality testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from langsmith import traceable
from langsmith.wrappers import wrap_openai
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize LangSmith tracing
import os
if os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true":
    print("✅ LangSmith tracing enabled")
else:
    print("⚠️ LangSmith tracing not enabled. Set LANGCHAIN_TRACING_V2=true to enable.")

app = FastAPI(title="Banking RAG Server with OpenAI")

# Initialize OpenAI client
openai_client = None
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key and openai_api_key != "placeholder" and not openai_api_key.startswith("sk-placeholder"):
        openai_client = OpenAI(api_key=openai_api_key)
        # Wrap OpenAI client with LangSmith tracing
        if os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true":
            openai_client = wrap_openai(openai_client)
            print("✅ OpenAI client initialized with LangSmith tracing")
        else:
            print("✅ OpenAI client initialized successfully")
    else:
        print("⚠️ OpenAI API key not found or is placeholder. Using fallback responses.")
except Exception as e:
    print(f"❌ Failed to initialize OpenAI client: {e}")
    openai_client = None

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample banking data for testing
SAMPLE_BANKING_DATA = [
    {
        "content": "Loan underwriting process involves credit assessment, income verification, and risk analysis. Applicants must provide tax returns, bank statements, and employment verification.",
        "metadata": {"source": "Banking Policy Manual", "page": 45, "type": "underwriting"}
    },
    {
        "content": "Current mortgage rates: 30-year fixed at 6.5%, 15-year fixed at 6.0%, adjustable rate mortgages starting at 5.5%.",
        "metadata": {"source": "Rate Sheet", "page": 1, "type": "rates"}
    },
    {
        "content": "Compliance requirements for Know Your Customer (KYC): Identity verification, address confirmation, and beneficial ownership disclosure required.",
        "metadata": {"source": "Compliance Manual", "page": 12, "type": "compliance"}
    },
    {
        "content": "Risk management policies require stress testing for loan portfolios quarterly and maintaining capital adequacy ratios above 12%.",
        "metadata": {"source": "Risk Policy", "page": 8, "type": "risk"}
    }
]

class QueryRequest(BaseModel):
    question: str
    use_conversation: bool = False
    include_sources: bool = True
    k: int = 5

@app.get("/health")
@traceable(name="health_check")
async def health_check():
    """Health check endpoint with LangSmith tracing"""
    # Try to load processed documents if available
    doc_count = 0
    try:
        if os.path.exists("processed_documents.json"):
            with open("processed_documents.json", "r") as f:
                data = json.load(f)
                doc_count = len(data)
    except:
        pass
    
    langsmith_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    openai_available = openai_client is not None
    
    return {
        "status": "healthy",
        "system_ready": True,
        "vector_store_ready": True,
        "documents_in_store": doc_count,
        "sample_data_available": len(SAMPLE_BANKING_DATA),
        "langsmith_tracing": langsmith_enabled,
        "openai_available": openai_available,
        "uptime": "test_mode"
    }

@app.get("/search/tables")
@traceable(name="search_tables")
async def search_tables(query: str, k: int = 5):
    """Search for table-related content with LangSmith tracing"""
    result = search_content(query, k, "tables")
    # Generate AI response for search results
    if openai_client:
        try:
            ai_response = await generate_openai_response(f"Explain the table information about: {query}", result["results"] if "results" in result else [])
            result["ai_summary"] = ai_response
        except:
            pass
    return result

@app.get("/search/compliance")
@traceable(name="search_compliance")
async def search_compliance(query: str, k: int = 5):
    """Search for compliance-related content with LangSmith tracing"""
    result = search_content(query, k, "compliance")
    # Generate AI response for search results  
    if openai_client:
        try:
            ai_response = await generate_openai_response(f"Explain the compliance requirements for: {query}", result["results"] if "results" in result else [])
            result["ai_summary"] = ai_response
        except:
            pass
    return result

@app.post("/query")
@traceable(
    name="banking_rag_query",
    metadata={"pipeline": "banking_rag", "version": "v1.0"}
)
async def query_documents(request: QueryRequest):
    """Main Banking RAG pipeline endpoint with comprehensive LangSmith tracing"""
    
    # Generate unique session ID for tracing
    session_id = str(uuid.uuid4())
    
    # Log input parameters
    input_metadata = {
        "question": request.question,
        "k": request.k,
        "use_conversation": request.use_conversation,
        "include_sources": request.include_sources,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Step 1: Document Retrieval and Search
    result = search_content(request.question, request.k)
    
    # Step 2: Generate AI Response
    structured_response = await generate_ai_response(request.question, result["results"])
    
    # Step 3: Format Final Response
    if request.include_sources:
        formatted_response = {
            "response": structured_response,
            "sources": [
                {
                    "content": item["content"],
                    "source": item["metadata"].get("source", "Unknown"),
                    "page": item["metadata"].get("page", "N/A"),
                    "relevance_score": item["score"]
                }
                for item in result["results"]
            ],
            "query": request.question,
            "total_sources": result["total_found"],
            "session_id": session_id
        }
    else:
        formatted_response = {
            "response": structured_response,
            "query": request.question,
            "session_id": session_id
        }
    
    return formatted_response

@traceable(name="document_search")
def search_content(query: str, k: int = 5, content_type: str = ""):
    """Document search with comprehensive LangSmith tracing"""
    
    # Try to use processed documents first
    content_sources = []
    
    try:
        if os.path.exists("processed_documents.json"):
            with open("processed_documents.json", "r") as f:
                processed_docs = json.load(f)
                content_sources.extend(processed_docs)
    except:
        pass
    
    # Add sample data as fallback
    content_sources.extend(SAMPLE_BANKING_DATA)
    
    # Simple keyword matching with enhanced tracking
    query_words = query.lower().split()
    scored_results = []
    
    for item in content_sources:
        content = item.get("content", "").lower()
        metadata = item.get("metadata", {})
        
        # Filter by content type if specified
        if content_type and content_type != "tables":
            item_type = metadata.get("type", "")
            if content_type == "compliance" and "compliance" not in item_type and "regulatory" not in content:
                continue
        
        # Calculate simple score
        score = sum(1 for word in query_words if word in content)
        if score > 0:
            scored_results.append({
                "content": item["content"],
                "metadata": metadata,
                "score": score
            })
    
    # Sort by score and return top k
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    results = scored_results[:k]
    
    # Log search metrics
    search_metrics = {
        "total_documents_searched": len(content_sources),
        "matching_documents": len(scored_results),
        "returned_documents": len(results),
        "search_terms": len(query_words),
        "content_type_filter": content_type,
        "avg_relevance_score": sum(r["score"] for r in results) / len(results) if results else 0
    }
    
    return {
        "query": query,
        "results": results,
        "total_found": len(scored_results),
        "source": "processed_documents" if os.path.exists("processed_documents.json") else "sample_data",
        "search_metrics": search_metrics
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Banking RAG Test Server",
        "endpoints": ["/health", "/search/tables", "/search/compliance", "/query"],
        "status": "running"
    }

@traceable(name="ai_response_generation")
async def generate_ai_response(question: str, results: list) -> str:
    """Generate AI-powered response with comprehensive tracing"""
    
    if openai_client and results:
        try:
            return await generate_openai_response(question, results)
        except Exception as e:
            print(f"OpenAI error, falling back to structured response: {e}")
            return generate_structured_response(question, results)
    else:
        return generate_structured_response(question, results)

@traceable(
    name="openai_response_generation",
    metadata={"model_provider": "openai", "response_type": "banking_rag"}
)
async def generate_openai_response(question: str, results: list) -> str:
    """Generate response using OpenAI GPT with detailed LangSmith tracing"""
    
    if not results:
        return "I couldn't find specific information to answer your question. Please try rephrasing or provide more details."
    
    # Create context from top results
    context_parts = []
    context_metadata = []
    
    for i, result in enumerate(results[:4], 1):
        source = result["metadata"].get("source", "Unknown Document")
        page = result["metadata"].get("page", "N/A")
        content = result["content"]
        
        context_parts.append(f"""
Document {i}: {source} (Page {page})
Content: {content}
""")
        
        context_metadata.append({
            "document_index": i,
            "source": source,
            "page": page,
            "content_length": len(content),
            "relevance_score": result.get("score", 0)
        })
    
    context = "\n".join(context_parts)
    
    # Analyze question type for specialized prompting
    question_lower = question.lower()
    question_type = "general"
    
    if any(word in question_lower for word in ["rate", "interest", "pricing", "cost"]):
        question_type = "rates_pricing"
        system_prompt = """You are a banking expert specializing in interest rates and pricing. Provide detailed, accurate information about banking rates, fees, and pricing structures. Use specific numbers and percentages when available in the documents."""
    elif any(word in question_lower for word in ["loan", "credit", "lending", "product"]):
        question_type = "loan_products"
        system_prompt = """You are a banking expert specializing in loan products and credit services. Explain loan types, requirements, terms, and processes clearly. Focus on practical information customers need."""
    elif any(word in question_lower for word in ["compliance", "regulation", "requirement", "law"]):
        question_type = "compliance"
        system_prompt = """You are a banking compliance expert. Explain regulatory requirements, legal obligations, and compliance procedures clearly. Emphasize important regulatory details and consequences."""
    elif any(word in question_lower for word in ["risk", "management", "policy"]):
        question_type = "risk_management"
        system_prompt = """You are a banking risk management expert. Explain risk policies, assessment procedures, and mitigation strategies. Focus on practical risk management approaches."""
    else:
        system_prompt = """You are a knowledgeable banking expert. Provide comprehensive, accurate information based on banking documents. Be helpful and professional."""
    
    user_prompt = f"""Based on the following banking documents, please answer this question: "{question}"

Document Context:
{context}

Instructions:
1. Provide a comprehensive, well-structured answer
2. Use markdown formatting (##, **, bullet points)
3. Include specific details and examples from the documents
4. Cite sources when possible (e.g., "According to the Banking Law document...")
5. If information is incomplete, mention what additional details might be needed
6. Be professional and banking-appropriate in tone
7. Structure your response with clear sections and headings

Answer:"""

    # Create comprehensive metadata for tracing
    generation_metadata = {
        "question_type": question_type,
        "context_length": len(context),
        "num_documents": len(context_parts),
        "document_sources": context_metadata,
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0.3,
        "max_tokens": 1200
    }

    try:
        if not openai_client:
            raise Exception("OpenAI client not initialized")
            
        # Note: OpenAI client is already wrapped with LangSmith tracing
        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1200,
            presence_penalty=0.1,
            frequency_penalty=0.1,
            metadata=generation_metadata  # Pass metadata to LangSmith
        )
        
        ai_response = response.choices[0].message.content
        final_response = ai_response or "I apologize, but I couldn't generate a proper response. Please try again."
        
        # Log response metrics
        response_metadata = {
            "response_length": len(final_response),
            "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else 0,
            "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') and response.usage else 0
        }
        
        return final_response
        
    except Exception as e:
        error_metadata = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "fallback_used": False
        }
        print(f"OpenAI API error: {e}")
        raise e

def generate_structured_response(question: str, results: list) -> str:
    """Generate a structured response based on the question and results"""
    
    if not results:
        return f"I couldn't find specific information about {question.lower()} in the available banking documents. Please try rephrasing your question or contact your banking specialist for detailed information."
    
    # Analyze question type
    question_lower = question.lower()
    
    # Create structured response based on content
    if any(word in question_lower for word in ["rate", "interest", "pricing", "cost"]):
        return generate_rates_response(question, results)
    elif any(word in question_lower for word in ["loan", "credit", "lending", "product"]):
        return generate_loan_products_response(question, results)
    elif any(word in question_lower for word in ["compliance", "regulation", "requirement", "law"]):
        return generate_compliance_response(question, results)
    elif any(word in question_lower for word in ["underwriting", "process", "procedure"]):
        return generate_process_response(question, results)
    elif any(word in question_lower for word in ["risk", "management", "policy"]):
        return generate_risk_response(question, results)
    else:
        return generate_general_response(question, results)

def generate_rates_response(question: str, results: list) -> str:
    """Generate response for rate-related queries"""
    response = f"## Interest Rates and Pricing Information\n\n"
    response += "Based on the banking documents, here's what I found about current rates:\n\n"
    
    rate_info = []
    for result in results[:3]:
        content = result["content"]
        source = result["metadata"].get("source", "Unknown")
        
        if any(word in content.lower() for word in ["rate", "interest", "%", "pricing", "apr"]):
            rate_info.append(f"• **{source}**: {extract_key_info(content, 100)}")
    
    if rate_info:
        response += "\n".join(rate_info)
    else:
        response += "• Current rate information varies by product type and customer profile\n"
        response += "• Rates are subject to change based on market conditions\n"
        response += "• Contact your banker for the most current rate quotes"
    
    response += "\n\n📋 **Key Points:**\n"
    response += "- Interest rates may vary based on loan type, term, and creditworthiness\n"
    response += "- Fixed vs. variable rate options may be available\n"
    response += "- Rate changes are subject to regulatory and market conditions\n"
    
    return response

def generate_loan_products_response(question: str, results: list) -> str:
    """Generate response for loan product queries"""
    response = f"## Loan Products and Services\n\n"
    
    products = []
    features = []
    
    for result in results[:4]:
        content = result["content"]
        source = result["metadata"].get("source", "Unknown")
        
        if any(word in content.lower() for word in ["mortgage", "loan", "credit", "financing"]):
            key_info = extract_key_info(content, 120)
            products.append(f"• **{source}**: {key_info}")
        
        if any(word in content.lower() for word in ["feature", "benefit", "term", "condition"]):
            features.append(extract_key_info(content, 80))
    
    if products:
        response += "**Available Products:**\n"
        response += "\n".join(products[:3])
        response += "\n\n"
    
    response += "**Key Features:**\n"
    response += "• Flexible loan terms and repayment schedules\n"
    response += "• Competitive interest rates based on creditworthiness\n"
    response += "• Various loan types including personal, business, and mortgage loans\n"
    response += "• Professional underwriting and quick approval processes\n\n"
    
    response += "📞 **Next Steps:**\n"
    response += "- Consult with a loan officer for personalized options\n"
    response += "- Prepare required documentation for application\n"
    response += "- Review terms and conditions carefully before proceeding"
    
    return response

def generate_compliance_response(question: str, results: list) -> str:
    """Generate response for compliance queries"""
    response = f"## Regulatory Compliance Information\n\n"
    
    requirements = []
    for result in results[:3]:
        content = result["content"]
        source = result["metadata"].get("source", "Unknown")
        
        key_info = extract_key_info(content, 100)
        requirements.append(f"• **{source}**: {key_info}")
    
    if requirements:
        response += "**Compliance Requirements:**\n"
        response += "\n".join(requirements)
        response += "\n\n"
    
    response += "**Important Compliance Areas:**\n"
    response += "• Know Your Customer (KYC) requirements\n"
    response += "• Anti-Money Laundering (AML) procedures\n"
    response += "• Documentation and record-keeping standards\n"
    response += "• Risk assessment and management protocols\n\n"
    
    response += "⚖️ **Regulatory Note:**\n"
    response += "All banking operations must comply with applicable federal and state regulations. "
    response += "Consult with compliance officers for specific requirements."
    
    return response

def generate_process_response(question: str, results: list) -> str:
    """Generate response for process-related queries"""
    response = f"## Banking Process Information\n\n"
    
    steps = []
    for i, result in enumerate(results[:3], 1):
        content = result["content"]
        key_info = extract_key_info(content, 120)
        steps.append(f"**Step {i}**: {key_info}")
    
    if steps:
        response += "\n\n".join(steps)
        response += "\n\n"
    
    response += "📝 **General Process Guidelines:**\n"
    response += "• Complete all required documentation\n"
    response += "• Provide accurate and up-to-date information\n"
    response += "• Allow sufficient time for review and approval\n"
    response += "• Maintain communication with your banking representative\n"
    
    return response

def generate_risk_response(question: str, results: list) -> str:
    """Generate response for risk management queries"""
    response = f"## Risk Management Information\n\n"
    
    policies = []
    for result in results[:3]:
        content = result["content"]
        source = result["metadata"].get("source", "Unknown")
        key_info = extract_key_info(content, 100)
        policies.append(f"• **{source}**: {key_info}")
    
    if policies:
        response += "**Risk Management Policies:**\n"
        response += "\n".join(policies)
        response += "\n\n"
    
    response += "**Key Risk Areas:**\n"
    response += "• Credit risk assessment and mitigation\n"
    response += "• Operational risk management\n"
    response += "• Market risk monitoring\n"
    response += "• Liquidity risk controls\n\n"
    
    response += "⚠️ **Risk Management Priority:**\n"
    response += "Regular monitoring and assessment of all risk factors to ensure sound banking practices."
    
    return response

def generate_general_response(question: str, results: list) -> str:
    """Generate general response for other queries"""
    response = f"## Banking Information Summary\n\n"
    response += f"Here's what I found regarding: **{question}**\n\n"
    
    key_points = []
    for result in results[:4]:
        content = result["content"]
        source = result["metadata"].get("source", "Unknown")
        key_info = extract_key_info(content, 100)
        key_points.append(f"• **{source}**: {key_info}")
    
    if key_points:
        response += "\n".join(key_points)
    else:
        response += "• Information available in banking documentation\n"
        response += "• Contact your banking representative for specific details"
    
    response += "\n\n📚 **For More Information:**\n"
    response += "Please refer to the source documents or contact your banking specialist for detailed guidance."
    
    return response

def extract_key_info(content: str, max_length: int = 100) -> str:
    """Extract key information from content"""
    # Clean up the content
    content = content.replace('\n', ' ').strip()
    
    # If content is short enough, return it
    if len(content) <= max_length:
        return content
    
    # Find sentence breaks near the max length
    sentences = content.split('. ')
    result = ""
    
    for sentence in sentences:
        if len(result + sentence + '. ') <= max_length:
            result += sentence + '. '
        else:
            break
    
    if not result:
        result = content[:max_length-3] + "..."
    
    return result.strip()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 