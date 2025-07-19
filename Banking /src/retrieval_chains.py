"""
Advanced Retrieval Chains for Banking RAG System
Implements RetrievalQA, ConversationalRetrievalChain, hybrid search, and reranking
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
from datetime import datetime
import json

from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.retrievers import BaseRetriever
from langchain.schema.runnable import Runnable

from src.config import get_settings
from src.vectorstore import BankingVectorStore

settings = get_settings()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BankingRetriever(BaseRetriever):
    """
    Advanced retriever for banking documents with hybrid search and reranking
    """
    
    def __init__(
        self,
        vector_store: BankingVectorStore,
        search_type: str = "hybrid",
        k: int = 5,
        score_threshold: Optional[float] = None,
        enable_reranking: bool = True,
        compliance_boost: float = 1.2,
        table_boost: float = 1.1
    ):
        super().__init__()
        self.vector_store = vector_store
        self.search_type = search_type
        self.k = k
        self.score_threshold = score_threshold
        self.enable_reranking = enable_reranking
        self.compliance_boost = compliance_boost
        self.table_boost = table_boost
    
    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        """Get relevant documents based on query"""
        
        # Determine search strategy based on query content
        search_strategy = self._determine_search_strategy(query)
        
        # Perform search based on strategy
        if search_strategy == "compliance":
            documents = self._search_compliance(query)
        elif search_strategy == "tables":
            documents = self._search_tables(query)
        elif search_strategy == "hybrid":
            documents = self._search_hybrid(query)
        else:
            documents = self._search_similarity(query)
        
        # Apply reranking if enabled
        if self.enable_reranking and documents:
            documents = self._rerank_documents(documents, query)
        
        # Apply score threshold filtering
        if self.score_threshold:
            documents = self._filter_by_score(documents, self.score_threshold)
        
        return documents
    
    def _determine_search_strategy(self, query: str) -> str:
        """Determine the best search strategy based on query content"""
        query_lower = query.lower()
        
        # Check for compliance-related queries
        compliance_terms = ["regulation", "compliance", "requirement", "policy", "audit", "risk"]
        if any(term in query_lower for term in compliance_terms):
            return "compliance"
        
        # Check for table-related queries
        table_terms = ["rate", "table", "schedule", "matrix", "pricing", "amortization"]
        if any(term in query_lower for term in table_terms):
            return "tables"
        
        # Default to hybrid search
        return "hybrid"
    
    def _search_compliance(self, query: str) -> List[Document]:
        """Search compliance-relevant documents"""
        try:
            return self.vector_store.search_compliance(query, k=self.k)
        except Exception as e:
            logger.warning(f"Compliance search failed: {e}")
            return self._search_similarity(query)
    
    def _search_tables(self, query: str) -> List[Document]:
        """Search table-containing documents"""
        try:
            return self.vector_store.search_tables(query, k=self.k)
        except Exception as e:
            logger.warning(f"Table search failed: {e}")
            return self._search_similarity(query)
    
    def _search_hybrid(self, query: str) -> List[Document]:
        """Perform hybrid search"""
        try:
            results = self.vector_store.hybrid_search(query, k=self.k)
            return [doc for doc, score in results]
        except Exception as e:
            logger.warning(f"Hybrid search failed: {e}")
            return self._search_similarity(query)
    
    def _search_similarity(self, query: str) -> List[Document]:
        """Fallback similarity search"""
        try:
            return self.vector_store.similarity_search(query, k=self.k)
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def _rerank_documents(self, documents: List[Document], query: str) -> List[Document]:
        """Rerank documents based on banking-specific relevance"""
        
        if not documents:
            return documents
        
        # Calculate relevance scores
        scored_docs = []
        for doc in documents:
            score = self._calculate_relevance_score(doc, query)
            scored_docs.append((doc, score))
        
        # Sort by score (descending)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return reranked documents
        return [doc for doc, score in scored_docs]
    
    def _calculate_relevance_score(self, document: Document, query: str) -> float:
        """Calculate relevance score for reranking"""
        base_score = 1.0
        
        metadata = document.metadata
        content = document.page_content.lower()
        query_lower = query.lower()
        
        # Boost for compliance documents if query is compliance-related
        if (metadata.get("compliance_relevant", False) and 
            any(term in query_lower for term in ["compliance", "regulation", "policy"])):
            base_score *= self.compliance_boost
        
        # Boost for table documents if query mentions rates, tables, etc.
        if (metadata.get("contains_table", False) and 
            any(term in query_lower for term in ["rate", "table", "schedule", "pricing"])):
            base_score *= self.table_boost
        
        # Boost for exact topic matches
        doc_topic = metadata.get("semantic_topic", "")
        if doc_topic and doc_topic in query_lower:
            base_score *= 1.3
        
        # Boost for high-risk compliance content if appropriate
        if (metadata.get("risk_level") == "high" and 
            any(term in query_lower for term in ["risk", "violation", "penalty"])):
            base_score *= 1.4
        
        # Content relevance (simple keyword matching boost)
        query_terms = query_lower.split()
        content_matches = sum(1 for term in query_terms if term in content)
        if content_matches > 0:
            base_score *= (1 + 0.1 * content_matches / len(query_terms))
        
        return base_score
    
    def _filter_by_score(self, documents: List[Document], threshold: float) -> List[Document]:
        """Filter documents by relevance score threshold"""
        # This would require access to scores from the search results
        # For now, return all documents
        return documents

class BankingQAChain:
    """
    Banking-specific Question Answering chain with specialized prompts
    """
    
    def __init__(
        self,
        vector_store: BankingVectorStore,
        llm_model: str = "gpt-4-turbo-preview",
        temperature: float = 0.1,
        enable_compliance_checking: bool = True
    ):
        self.vector_store = vector_store
        self.enable_compliance_checking = enable_compliance_checking
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature,
            api_key=settings.openai_api_key
        )
        
        # Initialize retriever
        self.retriever = BankingRetriever(vector_store)
        
        # Create QA chain
        self.qa_chain = self._create_qa_chain()
    
    def _create_qa_chain(self) -> Runnable:
        """Create the QA chain with banking-specific prompts"""
        
        # Banking-specific QA prompt
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{question}")
        ])
        
        # Create stuff documents chain
        document_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        # Create retrieval chain
        retrieval_chain = create_retrieval_chain(self.retriever, document_chain)
        
        return retrieval_chain
    
    def _get_system_prompt(self) -> str:
        """Get banking-specific system prompt"""
        return """You are an expert AI assistant specializing in banking and financial services. You have access to a comprehensive knowledge base of banking documents, including loan handbooks, regulatory requirements, policy documents, and rate sheets.

INSTRUCTIONS:
1. Provide accurate, professional responses based strictly on the retrieved documents
2. When answering questions about rates, terms, or compliance requirements, cite specific tables or sections when available
3. If information involves regulatory compliance, clearly indicate the regulatory context
4. For rate-related queries, present information in a clear, structured format
5. If cross-references are mentioned in the documents (like "see Table 3.2"), try to incorporate that context
6. Always maintain confidentiality and professional standards
7. If you cannot find specific information in the documents, clearly state this rather than making assumptions

COMPLIANCE REQUIREMENTS:
- Never provide financial advice or recommendations
- Always emphasize that users should consult with qualified banking professionals
- Highlight any compliance or regulatory requirements mentioned in the documents
- Be precise with financial terms, rates, and regulatory requirements

RESPONSE FORMAT:
- Start with a direct answer to the question
- Provide supporting details from the documents
- Include relevant context from tables or rate sheets if applicable
- End with appropriate disclaimers if the topic involves compliance or rates

Context Documents:
{context}

Question: {question}

Provide a comprehensive, accurate answer based on the available documents."""
    
    def ask(self, question: str, **kwargs) -> Dict[str, Any]:
        """Ask a question and get an answer"""
        try:
            # Add compliance checking if enabled
            if self.enable_compliance_checking:
                question = self._add_compliance_context(question)
            
            result = self.qa_chain.invoke({"question": question})
            
            # Process and enhance the result
            enhanced_result = self._enhance_result(result, question)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"QA chain error: {e}")
            return {
                "answer": "I apologize, but I encountered an error processing your question. Please try rephrasing your question or contact support.",
                "error": str(e),
                "source_documents": []
            }
    
    def _add_compliance_context(self, question: str) -> str:
        """Add compliance context to questions when appropriate"""
        compliance_terms = ["regulation", "compliance", "requirement", "policy", "audit", "risk"]
        
        if any(term in question.lower() for term in compliance_terms):
            return f"{question}\n\nNote: Please ensure all compliance and regulatory aspects are addressed in the response."
        
        return question
    
    def _enhance_result(self, result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Enhance the result with additional metadata and processing"""
        
        enhanced = {
            "answer": result.get("answer", "No answer available"),
            "source_documents": result.get("context", []),
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "search_strategy": self.retriever._determine_search_strategy(question),
        }
        
        # Add source analysis
        if enhanced["source_documents"]:
            enhanced["source_analysis"] = self._analyze_sources(enhanced["source_documents"])
        
        # Add confidence indicator
        enhanced["confidence"] = self._calculate_confidence(result, question)
        
        return enhanced
    
    def _analyze_sources(self, documents: List[Document]) -> Dict[str, Any]:
        """Analyze the source documents used in the answer"""
        
        analysis = {
            "total_sources": len(documents),
            "document_types": {},
            "has_tables": False,
            "compliance_relevant": False,
            "risk_levels": {}
        }
        
        for doc in documents:
            metadata = doc.metadata
            
            # Document type analysis
            doc_type = metadata.get("document_type", "unknown")
            analysis["document_types"][doc_type] = analysis["document_types"].get(doc_type, 0) + 1
            
            # Table analysis
            if metadata.get("contains_table", False):
                analysis["has_tables"] = True
            
            # Compliance analysis
            if metadata.get("compliance_relevant", False):
                analysis["compliance_relevant"] = True
            
            # Risk level analysis
            risk_level = metadata.get("risk_level", "unknown")
            analysis["risk_levels"][risk_level] = analysis["risk_levels"].get(risk_level, 0) + 1
        
        return analysis
    
    def _calculate_confidence(self, result: Dict[str, Any], question: str) -> str:
        """Calculate confidence level of the answer"""
        
        documents = result.get("context", [])
        if not documents:
            return "low"
        
        # High confidence indicators
        high_confidence_indicators = 0
        
        # Check if we have multiple relevant sources
        if len(documents) >= 3:
            high_confidence_indicators += 1
        
        # Check if sources contain tables (for rate/numerical queries)
        if any(doc.metadata.get("contains_table", False) for doc in documents):
            high_confidence_indicators += 1
        
        # Check if sources are compliance documents (for compliance queries)
        compliance_terms = ["compliance", "regulation", "policy", "requirement"]
        if (any(term in question.lower() for term in compliance_terms) and
            any(doc.metadata.get("compliance_relevant", False) for doc in documents)):
            high_confidence_indicators += 1
        
        # Determine confidence level
        if high_confidence_indicators >= 2:
            return "high"
        elif high_confidence_indicators >= 1:
            return "medium"
        else:
            return "low"

class BankingConversationalChain:
    """
    Conversational retrieval chain for banking with memory and context management
    """
    
    def __init__(
        self,
        vector_store: BankingVectorStore,
        llm_model: str = "gpt-4-turbo-preview",
        memory_window: int = 10,
        max_memory_tokens: int = 2000
    ):
        self.vector_store = vector_store
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0.1,
            api_key=settings.openai_api_key
        )
        
        # Initialize retriever
        self.retriever = BankingRetriever(vector_store)
        
        # Initialize memory
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=max_memory_tokens,
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Create conversational chain
        self.conversation_chain = self._create_conversational_chain()
    
    def _create_conversational_chain(self) -> ConversationalRetrievalChain:
        """Create conversational retrieval chain"""
        
        # Banking-specific conversational prompt
        system_message = """You are a banking AI assistant with access to comprehensive banking documentation. 

CONVERSATION GUIDELINES:
- Maintain context from previous questions in the conversation
- Reference previous discussions when relevant
- For follow-up questions, consider the conversation history
- Always base answers on the retrieved documents
- Maintain professional banking standards throughout the conversation

BANKING EXPERTISE AREAS:
- Loan products and underwriting
- Interest rates and pricing
- Regulatory compliance
- Risk management
- Customer service policies
- Operational procedures

Remember: You should never provide financial advice, only information from the documents."""
        
        # Condense question prompt for chat history
        condense_question_prompt = PromptTemplate(
            template="""Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question that captures the relevant context from the chat history.

Chat History:
{chat_history}

Follow Up Input: {question}
Standalone question:""",
            input_variables=["chat_history", "question"]
        )
        
        # QA prompt
        qa_prompt = PromptTemplate(
            template=f"""{system_message}

Use the following pieces of context to answer the question at the end. If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.

Context:
{{context}}

Question: {{question}}
Helpful Answer:""",
            input_variables=["context", "question"]
        )
        
        # Create the conversational retrieval chain
        conversational_chain = ConversationalRetrievalChain(
            retriever=self.retriever,
            question_generator=self.llm,
            combine_docs_chain=self.llm,
            memory=self.memory,
            condense_question_prompt=condense_question_prompt,
            qa_prompt=qa_prompt,
            return_source_documents=True,
            verbose=True
        )
        
        return conversational_chain
    
    def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        """Have a conversation with the banking AI"""
        try:
            result = self.conversation_chain({"question": message})
            
            # Process and enhance result
            enhanced_result = {
                "answer": result["answer"],
                "source_documents": result.get("source_documents", []),
                "chat_history": self.memory.chat_memory.messages,
                "question": message,
                "timestamp": datetime.now().isoformat()
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Conversational chain error: {e}")
            return {
                "answer": "I apologize, but I encountered an error. Please try asking your question again.",
                "error": str(e),
                "source_documents": []
            }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        return self.memory.predict_new_summary(
            messages=self.memory.chat_memory.messages,
            existing_summary=""
        )

class BankingRAGPipeline:
    """
    Complete RAG pipeline for banking with multiple chain types
    """
    
    def __init__(
        self,
        vector_store: BankingVectorStore,
        enable_conversation: bool = True,
        enable_qa: bool = True
    ):
        self.vector_store = vector_store
        
        # Initialize chains
        self.qa_chain = BankingQAChain(vector_store) if enable_qa else None
        self.conversation_chain = BankingConversationalChain(vector_store) if enable_conversation else None
        
        # Track usage statistics
        self.usage_stats = {
            "qa_queries": 0,
            "conversation_turns": 0,
            "total_queries": 0,
            "error_count": 0
        }
    
    def ask_question(self, question: str, use_conversation: bool = False) -> Dict[str, Any]:
        """Ask a question using the appropriate chain"""
        
        self.usage_stats["total_queries"] += 1
        
        try:
            if use_conversation and self.conversation_chain:
                self.usage_stats["conversation_turns"] += 1
                result = self.conversation_chain.chat(question)
            elif self.qa_chain:
                self.usage_stats["qa_queries"] += 1
                result = self.qa_chain.ask(question)
            else:
                raise ValueError("No appropriate chain available")
            
            # Add pipeline metadata
            result["pipeline_type"] = "conversational" if use_conversation else "qa"
            result["usage_stats"] = self.usage_stats.copy()
            
            return result
            
        except Exception as e:
            self.usage_stats["error_count"] += 1
            logger.error(f"Pipeline error: {e}")
            return {
                "answer": "I apologize, but I encountered an error processing your question.",
                "error": str(e),
                "pipeline_type": "error"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline usage statistics"""
        return {
            **self.usage_stats,
            "vector_store_stats": self.vector_store.get_collection_stats()
        }

# Factory functions for easy initialization
def create_banking_qa_chain(vector_store: BankingVectorStore, **kwargs) -> BankingQAChain:
    """Create a banking QA chain"""
    return BankingQAChain(vector_store, **kwargs)

def create_banking_conversational_chain(vector_store: BankingVectorStore, **kwargs) -> BankingConversationalChain:
    """Create a banking conversational chain"""
    return BankingConversationalChain(vector_store, **kwargs)

def create_banking_rag_pipeline(vector_store: BankingVectorStore, **kwargs) -> BankingRAGPipeline:
    """Create a complete banking RAG pipeline"""
    return BankingRAGPipeline(vector_store, **kwargs)

# Example usage
if __name__ == "__main__":
    import asyncio
    from pathlib import Path
    from src.document_loaders import load_banking_documents
    from src.chunking_strategies import get_banking_chunker
    from src.vectorstore import get_banking_vector_store
    
    async def test_retrieval_chains():
        """Test the retrieval chains"""
        
        # Initialize vector store
        vector_store = get_banking_vector_store()
        
        # Load sample documents
        docs_path = Path(__file__).parent.parent / "Documents"
        if docs_path.exists():
            print("Testing retrieval chains...")
            
            # Create RAG pipeline
            pipeline = create_banking_rag_pipeline(vector_store)
            
            # Test questions
            test_questions = [
                "What are the current loan interest rates?",
                "What are the regulatory requirements for lending?",
                "Can you explain the amortization schedule?",
                "What compliance checks are required for new accounts?"
            ]
            
            print("\nTesting QA Chain:")
            for question in test_questions:
                print(f"\nQ: {question}")
                result = pipeline.ask_question(question, use_conversation=False)
                print(f"A: {result['answer'][:200]}...")
                if result.get('source_analysis'):
                    print(f"Sources: {result['source_analysis']['total_sources']} documents")
            
            print("\nTesting Conversational Chain:")
            for question in test_questions:
                print(f"\nQ: {question}")
                result = pipeline.ask_question(question, use_conversation=True)
                print(f"A: {result['answer'][:200]}...")
            
            print(f"\nPipeline Stats: {pipeline.get_stats()}")
            
        else:
            print("No documents directory found for testing")
    
    # Run the test
    asyncio.run(test_retrieval_chains()) 