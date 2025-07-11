# Medical Knowledge Assistant

A production-ready medical knowledge assistant that allows healthcare professionals to query medical documents, drug interactions, and clinical guidelines using a complete RAG (Retrieval-Augmented Generation) pipeline, evaluated with RAGAS, and deployed with real-time monitoring.

## Features

- 📄 Document Upload & Processing
  - Upload medical PDFs
  - Automatic text extraction and chunking
  - Metadata preservation (source, page, section)

- 💬 Intelligent Q&A
  - Natural language querying
  - Context-aware responses
  - Source citations
  - Safety checks and filtering

- 📊 Quality Metrics
  - RAGAS evaluation
  - Faithfulness scoring
  - Context precision
  - Answer relevance
  - Real-time monitoring

- 🔒 Safety Features
  - Blocks unsafe/unreliable answers
  - Filters experimental drug mentions
  - Validates dosage information
  - Requires high faithfulness scores

## Technology Stack

- Frontend: React.js + TailwindCSS
- Backend: FastAPI (Python)
- AI Pipeline: LangChain, OpenAI API, FAISS
- Evaluation: RAGAS
- Monitoring: Prometheus + Grafana
- Deployment: Docker + Docker Compose

## Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## Getting Started

1. Clone the repository:
```bash
git clone <repository-url>
cd medical-knowledge-assistant
```

2. Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your_api_key_here
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Grafana: http://localhost:3001

## Development Setup

### Backend

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend:
```bash
uvicorn app.main:app --reload
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm start
```

## Evaluation

Run the evaluation script to test the RAG pipeline:

```bash
python backend/app/eval.py test_questions.json
```

The script will generate an evaluation report with:
- Per-question metrics
- Overall success rate
- Average metric scores

## Monitoring

The Grafana dashboard displays:
- Query latency (p95)
- Answer quality metrics
- Blocked vs. accepted answers
- System health metrics

Default credentials:
- Username: admin
- Password: admin (change in production)

## API Endpoints

- `POST /upload`: Upload and process medical documents
- `POST /query`: Submit questions and get answers
- `GET /metrics`: Prometheus metrics endpoint
- `POST /batch-eval`: Run batch evaluation (admin only)

## Safety Guidelines

The system enforces strict safety measures:
- Minimum faithfulness score: 0.90
- Minimum context precision: 0.85
- Blocks experimental drug mentions
- Requires proper context for dosage information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)

## Acknowledgments

- OpenAI for the language models
- RAGAS team for the evaluation framework
- LangChain for the RAG pipeline tools 