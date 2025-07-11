from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile, Depends
from starlette.responses import RedirectResponse

from .config import get_settings, Settings
from .embeddings import DocumentIngestor
from .gmail_service import GmailService
from .scheduler import start_scheduler

app = FastAPI(title="Auto Email Responder")
settings = get_settings()


def check_credentials():
    """Verify required credentials are set."""
    missing = []
    if not settings.google_client_id:
        missing.append("GOOGLE_CLIENT_ID")
    if not settings.google_client_secret:
        missing.append("GOOGLE_CLIENT_SECRET")
    if not settings.openai_api_key:
        missing.append("OPENAI_API_KEY")
    
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required environment variables: {', '.join(missing)}. Please check your .env file."
        )


@app.on_event("startup")
async def startup_event():
    """Initialize services and verify configuration."""
    # Ensure uploaded_docs directory exists
    os.makedirs("uploaded_docs", exist_ok=True)
    
    # Start the email polling scheduler if credentials are configured
    if settings.google_client_id and settings.google_client_secret and settings.openai_api_key:
        start_scheduler()


# Dependency to get settings
async def get_verified_settings() -> Settings:
    check_credentials()
    return settings


@app.get("/authorize", summary="Initiate Gmail OAuth flow")
def authorize(settings: Settings = Depends(get_verified_settings)):
    """Start OAuth2 flow for Gmail access."""
    url = gmail_service.generate_auth_url()
    return RedirectResponse(url)


@app.get("/oauth2callback", summary="OAuth2 redirect handler")
def oauth2callback(code: str, settings: Settings = Depends(get_verified_settings)):
    """Handle OAuth2 callback from Google."""
    gmail_service.exchange_code(code)
    return {"detail": "Authorization successful"}


@app.post("/upload_policy", summary="Upload policy / FAQ documents")
async def upload_policy(
    files: List[UploadFile] = File(...),
    settings: Settings = Depends(get_verified_settings)
):
    """Upload and process company policy documents."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    saved: List[str] = []
    for file in files:
        if not file.filename:  # Type check for filename
            continue
            
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in {".txt", ".md", ".pdf"}:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        dest = os.path.join("uploaded_docs", file.filename)
        content = await file.read()
        
        with open(dest, "wb") as f:
            f.write(content)
            
        try:
            ingestor.ingest(dest)
            saved.append(dest)
        except Exception as e:
            os.unlink(dest)  # Clean up file if ingestion fails
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    return {"ingested": saved}


# Initialize services
ingestor = DocumentIngestor()
gmail_service = GmailService() 