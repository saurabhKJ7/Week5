from setuptools import setup, find_packages

# Define the core dependencies
install_requires = [
    "fastapi",
    "uvicorn[standard]",
    "pydantic",
    "python-multipart",
    "python-dotenv",
    "langchain",
    "langchain-openai",
    "langchain-community",
    "openai",
    "chromadb",
    "pdfplumber",
    "pandas",
    "nbformat",
    # Universal document processing
    "unstructured[docx,pptx,xlsx,pdf,md,html]",
    "openpyxl", # For Excel
    "python-pptx", # For PowerPoint
    # Image processing support
    "pytesseract",
    "pillow"
]

setup(
    name="notebook-llm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=install_requires,
    python_requires=">=3.8",
) 