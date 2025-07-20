#!/usr/bin/env python3
"""
LangSmith Setup Guide for Banking RAG System
Step-by-step guide to get proper LangSmith logging
"""

import os
import webbrowser

def setup_langsmith():
    """Guide user through LangSmith setup"""
    
    print("🔧 LangSmith Setup Guide for Banking RAG System")
    print("=" * 50)
    
    print("\n📋 Step 1: Get Your LangSmith API Key")
    print("1. Go to: https://smith.langchain.com/")
    print("2. Sign up or log in to your account")
    print("3. Go to Settings > API Keys")
    print("4. Create a new API key")
    print("5. Copy the API key (starts with 'ls__')")
    
    print("\n📋 Step 2: Get Your OpenAI API Key (Optional but Recommended)")
    print("1. Go to: https://platform.openai.com/api-keys")
    print("2. Create a new API key")
    print("3. Copy the API key (starts with 'sk-')")
    
    print("\n📋 Step 3: Update Your .env File")
    print("Replace the placeholder values in your .env file:")
    print("---")
    print("# LangSmith Configuration")
    print("LANGCHAIN_TRACING_V2=true")
    print("LANGCHAIN_API_KEY=ls__your-real-langsmith-key-here")
    print("LANGCHAIN_PROJECT=banking-rag-system")
    print()
    print("# OpenAI Configuration")
    print("OPENAI_API_KEY=sk-your-real-openai-key-here")
    print("---")
    
    print("\n📋 Step 4: Restart Your Server")
    print("pkill -f 'python simple_server.py' && python simple_server.py")
    
    print("\n📋 Step 5: Test LangSmith Integration")
    print("curl -X POST -H 'Content-Type: application/json' \\")
    print("  -d '{\"question\": \"What are the current interest rates?\", \"include_sources\": true}' \\")
    print("  http://localhost:8001/query")
    
    print("\n🌟 Benefits with Real API Keys:")
    print("✅ Full AI-powered responses (not just templates)")
    print("✅ Complete LangSmith tracing and observability")
    print("✅ No API errors in logs")
    print("✅ Production-ready monitoring")
    print("✅ Advanced evaluation capabilities")
    
    # Prompt to open browser
    response = input("\n🌐 Would you like me to open the LangSmith website? (y/n): ").lower()
    if response == 'y':
        print("Opening LangSmith website...")
        webbrowser.open('https://smith.langchain.com/')

if __name__ == "__main__":
    setup_langsmith() 