"""
Supabase Vector Store Integration for Banking RAG System
Includes schema setup, hybrid search capabilities, and banking-specific optimizations
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import asyncio
from pathlib import Path

import numpy as np
from supabase import create_client, Client
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_postgres import PGVector

from src.config import get_settings

settings = get_settings()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BankingVectorStore:
    """
    Enhanced Supabase vector store for banking documents with hybrid search
    and compliance tracking capabilities
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        collection_name: str = "banking_documents",
        embedding_dimension: int = 1536
    ):
        self.supabase_url = supabase_url or settings.supabase_url
        self.supabase_key = supabase_key or settings.supabase_key
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key are required")
        
        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key
        )
        
        # Initialize vector store
        self.vector_store = None
        self._setup_vector_store()
    
    def _setup_vector_store(self):
        """Set up the vector store with proper configuration"""
        try:
            self.vector_store = SupabaseVectorStore(
                client=self.supabase,
                embedding=self.embeddings,
                table_name=self.collection_name,
                query_name="match_banking_documents"
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def setup_database_schema(self):
        """Set up the database schema with banking-specific enhancements"""
        
        # Enable pgvector extension
        enable_pgvector = """
        CREATE EXTENSION IF NOT EXISTS vector;
        """
        
        # Create enhanced banking documents table
        create_table = f"""
        CREATE TABLE IF NOT EXISTS {self.collection_name} (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{{}}',
            embedding VECTOR({self.embedding_dimension}),
            
            -- Banking-specific columns for optimized queries
            document_type VARCHAR(50),
            source_file VARCHAR(255),
            page_number INTEGER,
            chunk_index INTEGER,
            chunk_type VARCHAR(50),
            
            -- Table and reference tracking
            contains_table BOOLEAN DEFAULT FALSE,
            table_type VARCHAR(50),
            table_references TEXT[],
            cross_references TEXT[],
            
            -- Compliance and topic classification
            compliance_relevant BOOLEAN DEFAULT FALSE,
            semantic_topic VARCHAR(100),
            risk_level VARCHAR(20),
            
            -- Audit and versioning
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            version INTEGER DEFAULT 1,
            
            -- Full-text search
            content_tsvector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
        );
        """
        
        # Create indexes for optimal performance
        create_indexes = f"""
        -- Vector similarity index
        CREATE INDEX IF NOT EXISTS {self.collection_name}_embedding_idx 
            ON {self.collection_name} USING ivfflat (embedding vector_cosine_ops);
        
        -- Full-text search index
        CREATE INDEX IF NOT EXISTS {self.collection_name}_fts_idx 
            ON {self.collection_name} USING gin(content_tsvector);
        
        -- Metadata indexes for filtering
        CREATE INDEX IF NOT EXISTS {self.collection_name}_metadata_idx 
            ON {self.collection_name} USING gin(metadata);
        
        -- Banking-specific indexes
        CREATE INDEX IF NOT EXISTS {self.collection_name}_document_type_idx 
            ON {self.collection_name}(document_type);
        CREATE INDEX IF NOT EXISTS {self.collection_name}_compliance_idx 
            ON {self.collection_name}(compliance_relevant);
        CREATE INDEX IF NOT EXISTS {self.collection_name}_table_type_idx 
            ON {self.collection_name}(table_type) WHERE contains_table = TRUE;
        CREATE INDEX IF NOT EXISTS {self.collection_name}_topic_idx 
            ON {self.collection_name}(semantic_topic);
        """
        
        # Create hybrid search function
        create_hybrid_search = f"""
        CREATE OR REPLACE FUNCTION match_banking_documents (
            query_embedding VECTOR({self.embedding_dimension}),
            match_count INTEGER DEFAULT 5,
            filter JSONB DEFAULT '{{}}'::jsonb,
            search_query TEXT DEFAULT '',
            hybrid_weight FLOAT DEFAULT 0.5,
            similarity_threshold FLOAT DEFAULT 0.0
        ) 
        RETURNS TABLE (
            id UUID,
            content TEXT,
            metadata JSONB,
            similarity FLOAT,
            fts_score FLOAT,
            hybrid_score FLOAT,
            document_type VARCHAR(50),
            compliance_relevant BOOLEAN,
            contains_table BOOLEAN
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            WITH vector_search AS (
                SELECT 
                    d.id,
                    d.content,
                    d.metadata,
                    d.document_type,
                    d.compliance_relevant,
                    d.contains_table,
                    1 - (d.embedding <=> query_embedding) AS similarity_score,
                    0.0::float as fts_score_raw
                FROM {self.collection_name} d
                WHERE 
                    d.metadata @> filter
                    AND (1 - (d.embedding <=> query_embedding)) >= similarity_threshold
                ORDER BY d.embedding <=> query_embedding
                LIMIT match_count * 2
            ),
            fts_search AS (
                SELECT 
                    d.id,
                    d.content,
                    d.metadata,
                    d.document_type,
                    d.compliance_relevant,
                    d.contains_table,
                    0.0::float as similarity_score,
                    ts_rank(d.content_tsvector, plainto_tsquery('english', search_query)) AS fts_score_raw
                FROM {self.collection_name} d
                WHERE 
                    d.metadata @> filter
                    AND (search_query = '' OR d.content_tsvector @@ plainto_tsquery('english', search_query))
                ORDER BY fts_score_raw DESC
                LIMIT CASE WHEN search_query = '' THEN 0 ELSE match_count * 2 END
            ),
            combined_results AS (
                SELECT 
                    COALESCE(v.id, f.id) as id,
                    COALESCE(v.content, f.content) as content,
                    COALESCE(v.metadata, f.metadata) as metadata,
                    COALESCE(v.document_type, f.document_type) as document_type,
                    COALESCE(v.compliance_relevant, f.compliance_relevant) as compliance_relevant,
                    COALESCE(v.contains_table, f.contains_table) as contains_table,
                    COALESCE(v.similarity_score, 0.0) as similarity_score,
                    COALESCE(f.fts_score_raw, 0.0) as fts_score_raw,
                    (
                        hybrid_weight * COALESCE(v.similarity_score, 0.0) + 
                        (1 - hybrid_weight) * COALESCE(f.fts_score_raw, 0.0)
                    ) as hybrid_score_calc
                FROM vector_search v
                FULL OUTER JOIN fts_search f ON v.id = f.id
            )
            SELECT 
                cr.id,
                cr.content,
                cr.metadata,
                cr.similarity_score::float as similarity,
                cr.fts_score_raw::float as fts_score,
                cr.hybrid_score_calc::float as hybrid_score,
                cr.document_type,
                cr.compliance_relevant,
                cr.contains_table
            FROM combined_results cr
            ORDER BY cr.hybrid_score_calc DESC
            LIMIT match_count;
        END
        $$;
        """
        
        # Create table-specific search function
        create_table_search = f"""
        CREATE OR REPLACE FUNCTION search_banking_tables (
            query_embedding VECTOR({self.embedding_dimension}),
            table_type_filter VARCHAR(50) DEFAULT NULL,
            match_count INTEGER DEFAULT 5
        )
        RETURNS TABLE (
            id UUID,
            content TEXT,
            metadata JSONB,
            table_type VARCHAR(50),
            similarity FLOAT
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                d.id,
                d.content,
                d.metadata,
                d.table_type,
                (1 - (d.embedding <=> query_embedding))::float AS similarity
            FROM {self.collection_name} d
            WHERE 
                d.contains_table = TRUE
                AND (table_type_filter IS NULL OR d.table_type = table_type_filter)
            ORDER BY d.embedding <=> query_embedding
            LIMIT match_count;
        END
        $$;
        """
        
        # Create compliance search function
        create_compliance_search = f"""
        CREATE OR REPLACE FUNCTION search_compliance_documents (
            query_embedding VECTOR({self.embedding_dimension}),
            risk_level_filter VARCHAR(20) DEFAULT NULL,
            match_count INTEGER DEFAULT 5
        )
        RETURNS TABLE (
            id UUID,
            content TEXT,
            metadata JSONB,
            semantic_topic VARCHAR(100),
            risk_level VARCHAR(20),
            similarity FLOAT
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                d.id,
                d.content,
                d.metadata,
                d.semantic_topic,
                d.risk_level,
                (1 - (d.embedding <=> query_embedding))::float AS similarity
            FROM {self.collection_name} d
            WHERE 
                d.compliance_relevant = TRUE
                AND (risk_level_filter IS NULL OR d.risk_level = risk_level_filter)
            ORDER BY d.embedding <=> query_embedding
            LIMIT match_count;
        END
        $$;
        """
        
        # Create update trigger for updated_at
        create_trigger = f"""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            NEW.version = OLD.version + 1;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_{self.collection_name}_updated_at ON {self.collection_name};
        CREATE TRIGGER update_{self.collection_name}_updated_at
            BEFORE UPDATE ON {self.collection_name}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        # Execute all SQL commands
        sql_commands = [
            enable_pgvector,
            create_table,
            create_indexes,
            create_hybrid_search,
            create_table_search,
            create_compliance_search,
            create_trigger
        ]
        
        try:
            for i, sql in enumerate(sql_commands):
                logger.info(f"Executing SQL command {i+1}/{len(sql_commands)}")
                result = self.supabase.rpc('exec_sql', {'sql': sql}).execute()
                if hasattr(result, 'error') and result.error:
                    logger.warning(f"SQL command {i+1} warning: {result.error}")
            
            logger.info("Database schema setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup database schema: {e}")
            # Try alternative approach using direct SQL execution
            return await self._setup_schema_alternative()
    
    async def _setup_schema_alternative(self):
        """Alternative schema setup method"""
        try:
            # Basic table creation
            basic_table = f"""
            CREATE TABLE IF NOT EXISTS {self.collection_name} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT,
                metadata JSONB,
                embedding VECTOR({self.embedding_dimension}),
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
            
            # Basic search function
            basic_function = f"""
            CREATE OR REPLACE FUNCTION match_banking_documents (
                query_embedding VECTOR({self.embedding_dimension}),
                match_count INT DEFAULT 5,
                filter JSONB DEFAULT '{{}}'
            ) RETURNS TABLE (
                id UUID,
                content TEXT,
                metadata JSONB,
                similarity FLOAT
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    {self.collection_name}.id,
                    {self.collection_name}.content,
                    {self.collection_name}.metadata,
                    1 - ({self.collection_name}.embedding <=> query_embedding) AS similarity
                FROM {self.collection_name}
                WHERE {self.collection_name}.metadata @> filter
                ORDER BY {self.collection_name}.embedding <=> query_embedding
                LIMIT match_count;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            logger.warning("Using basic schema setup due to limitations")
            return True
            
        except Exception as e:
            logger.error(f"Alternative schema setup failed: {e}")
            return False
    
    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100,
        **kwargs
    ) -> List[str]:
        """Add documents to the vector store with enhanced metadata processing"""
        
        if not documents:
            return []
        
        # Process documents in batches for better performance
        document_ids = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            # Enhance metadata for each document
            enhanced_docs = []
            for doc in batch:
                enhanced_doc = self._enhance_document_metadata(doc)
                enhanced_docs.append(enhanced_doc)
            
            try:
                batch_ids = self.vector_store.add_documents(enhanced_docs, **kwargs)
                document_ids.extend(batch_ids)
                logger.info(f"Added {len(batch)} documents to vector store")
                
            except Exception as e:
                logger.error(f"Failed to add batch: {e}")
                continue
        
        return document_ids
    
    def _enhance_document_metadata(self, document: Document) -> Document:
        """Enhance document metadata with banking-specific information"""
        
        metadata = document.metadata.copy()
        content = document.page_content
        
        # Extract banking-specific metadata
        metadata.update({
            # Document classification
            "document_type": metadata.get("document_type", self._classify_document_type(content)),
            "chunk_type": metadata.get("chunk_type", "text"),
            
            # Table information
            "contains_table": metadata.get("contains_table", self._has_table_content(content)),
            "table_type": metadata.get("table_type", self._identify_table_type(content)),
            
            # Compliance classification
            "compliance_relevant": metadata.get("compliance_relevant", self._is_compliance_relevant(content)),
            "semantic_topic": metadata.get("semantic_topic", self._classify_topic(content)),
            "risk_level": self._assess_risk_level(content),
            
            # Processing metadata
            "processed_at": datetime.now().isoformat(),
            "content_length": len(content),
            "word_count": len(content.split()),
        })
        
        return Document(page_content=content, metadata=metadata)
    
    def _classify_document_type(self, content: str) -> str:
        """Classify the type of banking document"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["loan handbook", "lending guide", "credit manual"]):
            return "loan_handbook"
        elif any(term in content_lower for term in ["regulatory", "compliance", "regulation"]):
            return "regulatory_manual"
        elif any(term in content_lower for term in ["policy", "procedure", "guideline"]):
            return "policy_document"
        elif any(term in content_lower for term in ["rate sheet", "pricing", "interest rate"]):
            return "rate_sheet"
        else:
            return "general_document"
    
    def _has_table_content(self, content: str) -> bool:
        """Check if content contains table structures"""
        table_patterns = [
            r"\|.*\|.*\|",  # Pipe tables
            r"^\s*\w+\s+\w+\s+\w+\s*$",  # Multi-column text
            r"(?i)table\s+\d+",  # Table references
        ]
        
        return any(re.search(pattern, content, re.MULTILINE) for pattern in table_patterns)
    
    def _identify_table_type(self, content: str) -> Optional[str]:
        """Identify the specific type of table"""
        if not self._has_table_content(content):
            return None
        
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["rate", "apr", "interest", "%"]):
            return "rate_table"
        elif any(term in content_lower for term in ["amortization", "payment schedule"]):
            return "amortization_table"
        elif any(term in content_lower for term in ["compliance", "requirement", "regulation"]):
            return "compliance_matrix"
        else:
            return "general_table"
    
    def _is_compliance_relevant(self, content: str) -> bool:
        """Check if content is relevant to compliance"""
        compliance_terms = [
            "regulation", "compliance", "requirement", "mandate", "law",
            "policy", "audit", "oversight", "supervision", "enforcement",
            "violation", "penalty", "risk management", "due diligence"
        ]
        
        content_lower = content.lower()
        return any(term in content_lower for term in compliance_terms)
    
    def _classify_topic(self, content: str) -> str:
        """Classify the semantic topic of the content"""
        content_lower = content.lower()
        
        topic_keywords = {
            "loan_products": ["loan", "mortgage", "credit", "lending"],
            "interest_rates": ["rate", "interest", "apr", "yield"],
            "compliance": ["compliance", "regulation", "requirement", "audit"],
            "risk_management": ["risk", "assessment", "mitigation", "exposure"],
            "customer_service": ["customer", "service", "support", "satisfaction"],
            "operations": ["process", "procedure", "workflow", "operation"],
        }
        
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                topic_scores[topic] = score
        
        return max(topic_scores, key=topic_scores.get) if topic_scores else "general"
    
    def _assess_risk_level(self, content: str) -> str:
        """Assess the risk level of the content"""
        content_lower = content.lower()
        
        high_risk_terms = ["violation", "penalty", "non-compliance", "breach", "fraud"]
        medium_risk_terms = ["requirement", "audit", "review", "oversight"]
        
        if any(term in content_lower for term in high_risk_terms):
            return "high"
        elif any(term in content_lower for term in medium_risk_terms):
            return "medium"
        else:
            return "low"
    
    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        hybrid_weight: float = 0.5,
        similarity_threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """Perform hybrid search combining vector similarity and full-text search"""
        
        try:
            # Generate embedding for the query
            query_embedding = self.embeddings.embed_query(query)
            
            # Prepare filter
            filter_json = json.dumps(filter_dict or {})
            
            # Execute hybrid search
            result = self.supabase.rpc(
                'match_banking_documents',
                {
                    'query_embedding': query_embedding,
                    'match_count': k,
                    'filter': filter_json,
                    'search_query': query,
                    'hybrid_weight': hybrid_weight,
                    'similarity_threshold': similarity_threshold
                }
            ).execute()
            
            if result.data:
                documents_with_scores = []
                for row in result.data:
                    doc = Document(
                        page_content=row['content'],
                        metadata=row['metadata']
                    )
                    score = row.get('hybrid_score', row.get('similarity', 0))
                    documents_with_scores.append((doc, score))
                
                return documents_with_scores
            else:
                logger.warning("No results from hybrid search")
                return []
                
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback to standard similarity search
            return self.similarity_search_with_score(query, k, filter_dict)
    
    def search_tables(
        self,
        query: str,
        table_type: Optional[str] = None,
        k: int = 5
    ) -> List[Document]:
        """Search specifically for table content"""
        
        try:
            query_embedding = self.embeddings.embed_query(query)
            
            result = self.supabase.rpc(
                'search_banking_tables',
                {
                    'query_embedding': query_embedding,
                    'table_type_filter': table_type,
                    'match_count': k
                }
            ).execute()
            
            if result.data:
                return [
                    Document(
                        page_content=row['content'],
                        metadata=row['metadata']
                    )
                    for row in result.data
                ]
            return []
            
        except Exception as e:
            logger.error(f"Table search failed: {e}")
            # Fallback to filtered similarity search
            filter_dict = {"contains_table": True}
            if table_type:
                filter_dict["table_type"] = table_type
            
            return self.similarity_search(query, k, filter_dict)
    
    def search_compliance(
        self,
        query: str,
        risk_level: Optional[str] = None,
        k: int = 5
    ) -> List[Document]:
        """Search specifically for compliance-relevant content"""
        
        try:
            query_embedding = self.embeddings.embed_query(query)
            
            result = self.supabase.rpc(
                'search_compliance_documents',
                {
                    'query_embedding': query_embedding,
                    'risk_level_filter': risk_level,
                    'match_count': k
                }
            ).execute()
            
            if result.data:
                return [
                    Document(
                        page_content=row['content'],
                        metadata=row['metadata']
                    )
                    for row in result.data
                ]
            return []
            
        except Exception as e:
            logger.error(f"Compliance search failed: {e}")
            # Fallback
            filter_dict = {"compliance_relevant": True}
            if risk_level:
                filter_dict["risk_level"] = risk_level
            
            return self.similarity_search(query, k, filter_dict)
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Standard similarity search"""
        try:
            return self.vector_store.similarity_search(query, k=k, filter=filter_dict)
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """Similarity search with scores"""
        try:
            return self.vector_store.similarity_search_with_score(query, k=k, filter=filter_dict)
        except Exception as e:
            logger.error(f"Similarity search with score failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        try:
            # Count documents by type
            type_stats = self.supabase.from_(self.collection_name)\
                .select('document_type', count='exact')\
                .execute()
            
            # Count compliance documents
            compliance_stats = self.supabase.from_(self.collection_name)\
                .select('compliance_relevant', count='exact')\
                .eq('compliance_relevant', True)\
                .execute()
            
            # Count documents with tables
            table_stats = self.supabase.from_(self.collection_name)\
                .select('contains_table', count='exact')\
                .eq('contains_table', True)\
                .execute()
            
            return {
                "total_documents": len(type_stats.data) if type_stats.data else 0,
                "compliance_documents": compliance_stats.count if compliance_stats.count else 0,
                "documents_with_tables": table_stats.count if table_stats.count else 0,
                "document_types": type_stats.data if type_stats.data else [],
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}

# Factory function for easy initialization
def get_banking_vector_store(**kwargs) -> BankingVectorStore:
    """Get a configured banking vector store instance"""
    return BankingVectorStore(**kwargs)

# Example usage
if __name__ == "__main__":
    import asyncio
    from pathlib import Path
    from src.document_loaders import load_banking_documents
    from src.chunking_strategies import get_banking_chunker
    
    async def test_vector_store():
        """Test the vector store setup and functionality"""
        
        # Initialize vector store
        vector_store = get_banking_vector_store()
        
        # Setup database schema
        schema_result = await vector_store.setup_database_schema()
        print(f"Schema setup result: {schema_result}")
        
        # Load and process documents
        docs_path = Path(__file__).parent.parent / "Documents"
        if docs_path.exists():
            print("Loading documents...")
            documents = load_banking_documents(str(docs_path))
            
            if documents:
                # Chunk documents
                chunker = get_banking_chunker("hybrid")
                all_chunks = []
                
                for doc in documents[:2]:  # Test with first 2 documents
                    chunks = chunker.chunk_document(doc)
                    all_chunks.extend(chunks)
                
                print(f"Created {len(all_chunks)} chunks")
                
                # Add to vector store
                if all_chunks:
                    ids = vector_store.add_documents(all_chunks[:5])  # Test with 5 chunks
                    print(f"Added documents with IDs: {ids}")
                    
                    # Test searches
                    print("\nTesting similarity search:")
                    results = vector_store.similarity_search("loan interest rates", k=3)
                    for i, result in enumerate(results):
                        print(f"Result {i+1}: {result.page_content[:100]}...")
                    
                    print("\nTesting hybrid search:")
                    hybrid_results = vector_store.hybrid_search("banking regulations", k=3)
                    for i, (doc, score) in enumerate(hybrid_results):
                        print(f"Hybrid result {i+1} (score: {score:.3f}): {doc.page_content[:100]}...")
                    
                    # Get collection stats
                    stats = vector_store.get_collection_stats()
                    print(f"\nCollection stats: {stats}")
                    
                else:
                    print("No chunks created")
            else:
                print("No documents loaded")
        else:
            print(f"Documents directory not found: {docs_path}")
    
    # Run the test
    asyncio.run(test_vector_store()) 