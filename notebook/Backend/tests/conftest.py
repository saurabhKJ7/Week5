import pytest
import os
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["VECTOR_STORE_PATH"] = "test_vector_store"
    os.environ["UPLOAD_DIR"] = "test_uploads"
    
    # Create test directories
    os.makedirs("test_uploads", exist_ok=True)
    os.makedirs("test_vector_store", exist_ok=True)
    
    yield
    
    # Cleanup
    for path in ["test_uploads", "test_vector_store"]:
        if os.path.exists(path):
            for file in os.listdir(path):
                os.remove(os.path.join(path, file))
            os.rmdir(path) 