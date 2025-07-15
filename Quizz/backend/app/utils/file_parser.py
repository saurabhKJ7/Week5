import docx
import fitz  # PyMuPDF
import os

def extract_text(file_path: str, content_type: str) -> str:
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return ""

    try:
        if content_type == "application/pdf":
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text("text")
            return text
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        elif content_type == "text/plain":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return ""
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return "" 