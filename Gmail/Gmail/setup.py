from setuptools import setup, find_packages

setup(
    name="gmail-auto-responder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "python-dotenv",
        "openai",
        "faiss-cpu",
        "pydantic",
        "pydantic-settings",  # Added for BaseSettings
        "redis",
        "apscheduler",
        "python-multipart",
        "PyPDF2",
        "aiofiles",
    ],
) 