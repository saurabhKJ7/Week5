#!/usr/bin/env python3
"""
Script to help set up environment variables for Banking RAG System with LangSmith
"""

import os

def create_env_file():
    """Create .env file with proper LangSmith configuration"""
    
    env_content = """# Banking RAG System - Environment Configuration

# OpenAI Configuration (Required for AI responses)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# LangSmith Configuration (Required for tracing and evaluation)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=banking-rag-system
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Supabase Configuration (Optional - for production vector store)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_KEY=your-supabase-service-role-key-here

# Database Configuration (Optional)
DB_HOST=db.your-project-id.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-database-password

# Document Processing Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_TOKENS_PER_CHUNK=1000
PRESERVE_TABLES=true

# Retrieval Settings
RETRIEVAL_K=5
RERANK_K=3
SIMILARITY_THRESHOLD=0.7
ENABLE_HYBRID_SEARCH=true

# Cost Optimization Settings
ENABLE_EMBEDDING_CACHE=true
BATCH_SIZE=10
MAX_CONCURRENT_REQUESTS=3
CACHE_TTL=3600

# Banking Specific Settings
ENABLE_COMPLIANCE_MODE=true
REQUIRE_CITATIONS=true
MAX_CONTEXT_LENGTH=4000
BANKING_DOMAIN_BOOST=0.2
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file with LangSmith configuration")
    print("\n🔧 Next Steps:")
    print("1. Get your OpenAI API key from: https://platform.openai.com/api-keys")
    print("2. Get your LangSmith API key from: https://smith.langchain.com/")
    print("3. Replace the placeholder values in .env file")
    print("4. Restart your server: python simple_server.py")
    print("\n📊 Benefits with proper configuration:")
    print("• Full AI-powered responses instead of templates")
    print("• Comprehensive tracing and observability")
    print("• Performance monitoring and debugging")
    print("• Evaluation and testing frameworks")

if __name__ == "__main__":
    create_env_file() 