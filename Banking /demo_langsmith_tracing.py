#!/usr/bin/env python3
"""
Demo script to show LangSmith tracing in Banking RAG System
Shows what's being traced and logged currently
"""

import requests
import json
import time
from datetime import datetime

def demo_langsmith_tracing():
    """Demonstrate LangSmith tracing capabilities"""
    
    print("🔍 LangSmith Tracing Demo - Banking RAG System")
    print("=" * 60)
    
    # Test different types of queries to show tracing
    test_queries = [
        {
            "question": "What are the current mortgage interest rates?",
            "type": "Rates Query",
            "expected_traces": ["banking_rag_query", "document_search", "ai_response_generation"]
        },
        {
            "question": "What are the compliance requirements for KYC?", 
            "type": "Compliance Query",
            "expected_traces": ["search_compliance", "openai_response_generation"]
        },
        {
            "question": "Explain loan underwriting process",
            "type": "Process Query", 
            "expected_traces": ["banking_rag_query", "document_retrieval", "answer_generation"]
        }
    ]
    
    print(f"🚀 Running {len(test_queries)} traced queries...")
    print("\n📊 What's Being Traced:")
    print("• Query processing time and metadata")
    print("• Document search and retrieval metrics")  
    print("• AI response generation (attempts)")
    print("• Source document matching and scoring")
    print("• Session tracking with unique IDs")
    print("• Error handling and fallback responses")
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔄 Test {i}/{len(test_queries)}: {query['type']}")
        print(f"   Question: {query['question']}")
        
        start_time = time.time()
        
        try:
            # Make request to Banking RAG system
            response = requests.post(
                "http://localhost:8001/query",
                json={
                    "question": query["question"],
                    "use_conversation": False,
                    "include_sources": True,
                    "k": 5
                },
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    "query_type": query["type"],
                    "question": query["question"],
                    "response_time_ms": round(response_time * 1000, 2),
                    "response_length": len(data.get("response", "")),
                    "sources_found": len(data.get("sources", [])),
                    "session_id": data.get("session_id", "N/A"),
                    "total_sources_available": data.get("total_sources", 0),
                    "status": "success"
                }
                
                print(f"   ✅ Response Time: {result['response_time_ms']}ms")
                print(f"   📄 Response Length: {result['response_length']} chars")
                print(f"   📚 Sources Found: {result['sources_found']}")
                print(f"   🆔 Session ID: {result['session_id'][:8]}...")
                
            else:
                result = {
                    "query_type": query["type"],
                    "question": query["question"],
                    "status": "error",
                    "error_code": response.status_code
                }
                print(f"   ❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            result = {
                "query_type": query["type"], 
                "question": query["question"],
                "status": "error",
                "error": str(e)
            }
            print(f"   ❌ Error: {e}")
            
        results.append(result)
        time.sleep(1)  # Brief pause between requests
    
    # Summary
    print(f"\n📈 Tracing Summary:")
    print("=" * 30)
    
    successful_queries = [r for r in results if r["status"] == "success"]
    if successful_queries:
        avg_response_time = sum(r["response_time_ms"] for r in successful_queries) / len(successful_queries)
        total_sources = sum(r.get("sources_found", 0) for r in successful_queries)
        
        print(f"✅ Successful Queries: {len(successful_queries)}/{len(results)}")
        print(f"⏱️  Average Response Time: {avg_response_time:.2f}ms")
        print(f"📚 Total Sources Retrieved: {total_sources}")
        print(f"🔗 Unique Sessions: {len(set(r.get('session_id', '') for r in successful_queries))}")
    
    print(f"\n🔍 Current Tracing Status:")
    try:
        health_response = requests.get("http://localhost:8001/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"• LangSmith Tracing: {'✅ Enabled' if health_data.get('langsmith_tracing') else '❌ Disabled'}")
            print(f"• OpenAI Available: {'✅ Yes' if health_data.get('openai_available') else '❌ No'}")
            print(f"• Documents Loaded: {health_data.get('documents_in_store', 0):,}")
            print(f"• System Ready: {'✅ Yes' if health_data.get('system_ready') else '❌ No'}")
    except:
        print("• System Status: ❌ Cannot connect")
    
    print(f"\n📋 What You're Seeing in Logs:")
    print("• ✅ Function entry/exit tracing (@traceable decorators)")
    print("• ✅ Request metadata (session IDs, timestamps)")  
    print("• ✅ Document search metrics")
    print("• ✅ Response generation attempts")
    print("• ⚠️  API key errors (expected with placeholder keys)")
    print("• ✅ Fallback response generation")
    print("• ✅ Performance timing data")
    
    print(f"\n🎯 To Get Full LangSmith Dashboard:")
    print("1. Run: python setup_langsmith.py")
    print("2. Get real LangSmith API key from https://smith.langchain.com/")
    print("3. Update .env file with real API keys")
    print("4. Restart server and check LangSmith dashboard")
    
    # Save demo results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"langsmith_tracing_demo_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "demo_timestamp": datetime.now().isoformat(),
            "tracing_enabled": True,
            "results": results,
            "summary": {
                "total_queries": len(results),
                "successful_queries": len(successful_queries),
                "avg_response_time_ms": avg_response_time if successful_queries else 0
            }
        }, f, indent=2)
    
    print(f"\n💾 Demo results saved to: {results_file}")

if __name__ == "__main__":
    demo_langsmith_tracing() 