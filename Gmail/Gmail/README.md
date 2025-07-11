# Auto Email Responder

A production-ready system that connects to Gmail, semantically searches internal company policies/FAQs and auto-responds to incoming emails with OpenAI GPT models.

## Features
* OAuth2 Gmail integration – fetch unread emails, send replies, mark as read
* Upload markdown / PDF / text company documents, chunk & embed them to a FAISS vector index
* Semantic search to retrieve relevant policy chunks for every email
* GPT-3.5/4 powered response generation with professional tone
* Redis prompt-response cache to avoid regenerating duplicates
* Scheduler that polls Gmail every 5 minutes
* FastAPI backend with endpoints for OAuth2 flow and document upload

## Quick-start

1. Clone repository & setup virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

3. Copy `example.env` → `.env` and fill in your secrets:
   ```bash
   cp example.env .env
   # Edit .env with your credentials
   ```

4. Run the server:
   ```bash
   # From the project root:
   uvicorn app.main:app --reload
   ```

5. Open `http://localhost:8000/docs` for interactive docs.

6. Click `/authorize` to connect your Gmail account.

7. Upload policy files through `/upload_policy` or via Swagger UI.

## Deployment

Persist `token.pickle` and `vector_store.index` volumes, and connect to a managed Redis instance.

## Security Notes
* Do not commit `.env`, `token.pickle`, or any secrets.
* Restrict Gmail OAuth consent screen to your organisation.

## License
MIT 