#!/usr/bin/env python3
"""
Simple script to load banking documents into the RAG system
Works without requiring API keys by using basic document processing
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

def load_documents_directly():
    """Load documents directly without vector store requirements"""
    
    try:
        from src.document_loaders import BankingDocumentLoader
        from src.chunking_strategies import get_banking_chunker
    except Exception as e:
        print(f"Error importing modules: {e}")
        return False
    
    documents_path = Path("Documents")
    
    if not documents_path.exists():
        print("Documents folder not found!")
        return False
    
    # Initialize document loader
    print("Initializing document loader...")
    loader = BankingDocumentLoader()
    
    # Initialize chunking strategy  
    print("Setting up chunking strategy...")
    chunker = get_banking_chunker("hybrid")
    
    pdf_files = list(documents_path.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files to process:")
    
    all_chunks = []
    
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        
        try:
            # Load document
            documents = loader.load_documents(str(pdf_file))
            print(f"  Loaded {len(documents)} pages")
            
            # Chunk documents
            chunks = []
            for doc in documents:
                doc_chunks = chunker.chunk_document(doc)
                chunks.extend(doc_chunks)
            print(f"  Created {len(chunks)} chunks")
            
            all_chunks.extend(chunks)
            
        except Exception as e:
            print(f"  Error processing {pdf_file.name}: {e}")
            continue
    
    print(f"\n✅ Successfully processed {len(all_chunks)} total chunks from {len(pdf_files)} documents")
    
    # Save chunks to a simple JSON file for later use
    import json
    chunks_data = []
    for chunk in all_chunks:
        chunks_data.append({
            'content': chunk.page_content,
            'metadata': chunk.metadata
        })
    
    with open('processed_documents.json', 'w') as f:
        json.dump(chunks_data, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Chunks saved to 'processed_documents.json'")
    return True

def create_simple_demo():
    """Create a simple demo that works without external services"""
    
    try:
        import json
        with open('processed_documents.json', 'r') as f:
            chunks = json.load(f)
    except FileNotFoundError:
        print("❌ No processed documents found. Run document processing first.")
        return
    
    print(f"\n🏦 Banking RAG Demo - {len(chunks)} documents loaded")
    print("=" * 50)
    
    while True:
        query = input("\n💬 Ask about banking policies, rates, or compliance (or 'quit' to exit): ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
            
        if not query:
            continue
            
        # Simple keyword search through chunks
        relevant_chunks = []
        query_words = query.lower().split()
        
        for chunk in chunks:
            content_lower = chunk['content'].lower()
            score = sum(1 for word in query_words if word in content_lower)
            if score > 0:
                relevant_chunks.append((chunk, score))
        
        # Sort by relevance
        relevant_chunks.sort(key=lambda x: x[1], reverse=True)
        
        if relevant_chunks:
            print(f"\n📋 Found {len(relevant_chunks)} relevant sections:")
            for i, (chunk, score) in enumerate(relevant_chunks[:3]):  # Show top 3
                print(f"\n--- Result {i+1} (Score: {score}) ---")
                print(f"Source: {chunk['metadata'].get('source', 'Unknown')}")
                print(f"Page: {chunk['metadata'].get('page', 'N/A')}")
                print(f"Content: {chunk['content'][:500]}...")
        else:
            print("❌ No relevant information found. Try different keywords.")

if __name__ == "__main__":
    print("🏦 Banking Document Processor")
    print("=" * 40)
    
    choice = input("Choose:\n1. Process documents\n2. Run demo\n3. Both\nEnter (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        print("\n📚 Processing documents...")
        success = load_documents_directly()
        if not success:
            print("❌ Failed to process documents")
            sys.exit(1)
    
    if choice in ['2', '3']:
        create_simple_demo()
    
    print("\n👋 Done!") 