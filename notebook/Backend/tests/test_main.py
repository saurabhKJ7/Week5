import os
import json
from unittest.mock import patch, MagicMock
import pytest

# Set environment variables before importing app
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["ENVIRONMENT"] = "test"
os.environ["VECTOR_STORE_PATH"] = "test_vector_store"
os.environ["UPLOAD_DIR"] = "test_uploads"

# Create test directories
os.makedirs("test_uploads", exist_ok=True)
os.makedirs("test_vector_store", exist_ok=True)

# Mock OpenAI initialization
mock_embeddings = MagicMock()
mock_embeddings.embed_documents = lambda x: [[0.1] * 1536] * len(x)
mock_embeddings.embed_query = lambda x: [0.1] * 1536

# Mock ChatOpenAI
mock_chat = MagicMock()
mock_chat.invoke = MagicMock(return_value={"answer": "This is a test response"})

# Mock FAISS
mock_faiss = MagicMock()
mock_faiss.from_texts.return_value = MagicMock()
mock_faiss.from_texts.return_value.as_retriever.return_value = MagicMock()

# Mock ConversationalRetrievalChain
mock_chain = MagicMock()
mock_chain.return_value = {"answer": "This is a test response", "source_documents": []}

with patch("langchain_openai.OpenAIEmbeddings", return_value=mock_embeddings), \
     patch("langchain_openai.ChatOpenAI", return_value=mock_chat), \
     patch("langchain_community.vectorstores.FAISS", mock_faiss), \
     patch("langchain.chains.ConversationalRetrievalChain.from_llm", return_value=mock_chain):
    # Import app after mocking
    from fastapi.testclient import TestClient
    from app.main import app

    # Create test client
    client = TestClient(app)

    def test_read_root():
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "message": "Notebook LLM API is running"
        }

    def test_query_without_documents():
        response = client.post(
            "/query",
            json={"text": "What is this document about?", "context_size": 3}
        )
        assert response.status_code == 500
        assert "No documents have been processed yet" in response.json()["detail"]

    def test_upload_invalid_file():
        response = client.post(
            "/upload",
            files={"file": ("test.xyz", b"test content", "text/plain")}
        )
        assert response.status_code == 500
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_and_query():
        # First upload a text file
        response = client.post(
            "/upload",
            files={"file": ("test.txt", b"This is a test document about AI.", "text/plain")}
        )
        if response.status_code != 200:
            print("Upload Error Response:", response.json())
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Then query the uploaded content
        response = client.post(
            "/query",
            json={"text": "What is the document about?", "context_size": 1}
        )
        if response.status_code != 200:
            print("Query Error Response:", response.json())
        assert response.status_code == 200
        assert isinstance(response.json()["response"], str)

    def teardown_module(module):
        """Clean up test files after tests"""
        import shutil
        for path in ["test_uploads", "test_vector_store"]:
            if os.path.exists(path):
                shutil.rmtree(path) 