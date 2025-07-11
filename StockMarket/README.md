# AI-Powered Stock Market Chat Application

A real-time stock market chat application that combines live market data, news, and AI-powered insights to help users make informed investment decisions.

## Features

- 🚀 Real-time stock price updates via WebSocket
- 📈 Live market data from StockData.org
- 📰 Trending financial news from NewsAPI
- 🤖 AI-powered chat interface for market insights
- 📊 Interactive stock charts and dashboards
- 🔍 RAG (Retrieval Augmented Generation) for contextual responses
- 💾 Vector database for efficient news search
- 🔐 Secure authentication and API key management

## Tech Stack

### Backend
- FastAPI (Python)
- PostgreSQL (Database)
- ChromaDB (Vector Database)
- Redis (Caching)
- OpenAI GPT-4 (LLM)
- WebSocket for real-time updates

### Frontend
- Next.js 14
- TailwindCSS
- Chart.js
- SWR for data fetching
- TypeScript

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL
- Redis (optional)
- API Keys:
  - StockData.org API key
  - NewsAPI key
  - OpenAI API key

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd stockmarket
```

2. Backend Setup:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Frontend Setup:
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with your configuration
```

4. Database Setup:
```bash
# Create PostgreSQL database
createdb stockmarket_db

# Run migrations
python backend/scripts/db_init.py
```

5. Start the application:
```bash
# Start backend (from root directory)
uvicorn backend.main:app --reload

# Start frontend (in another terminal)
cd frontend
npm run dev
```

## API Documentation

The API documentation is available at `/docs` when running the backend server.

### Main Endpoints:
- `/api/v1/stocks/live` - Get real-time stock data
- `/api/v1/news/trending` - Get trending financial news
- `/api/v1/chat` - AI chat endpoint
- `/ws/stocks` - WebSocket endpoint for real-time updates

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   └── main.py
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/
├── requirements.txt
└── README.md
```

## Testing

```bash
# Run backend tests
pytest

# Run frontend tests
cd frontend
npm test
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT

## Acknowledgments

- StockData.org for real-time market data
- NewsAPI for financial news
- OpenAI for GPT-4 API 