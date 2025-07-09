# Expense Tracker

A FastAPI-based personal expense tracking application with a clean web interface.

## Features

- Track expenses with title, amount, category, and date
- View total expenses and category-wise breakdown
- Filter expenses by date range and category
- Beautiful UI with Bootstrap
- SQLite database for easy setup
- RESTful API endpoints

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn main:app --reload
```

4. Open your browser and navigate to:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Endpoints

- `GET /expenses`: List all expenses (optional date filters)
- `POST /expenses`: Create a new expense
- `PUT /expenses/{expense_id}`: Update an expense
- `DELETE /expenses/{expense_id}`: Delete an expense
- `GET /expenses/category/{category}`: Get expenses by category
- `GET /expenses/total`: Get total expenses with category breakdown

## Data Model

Expense:
- `id`: Integer (Primary Key)
- `title`: String
- `amount`: Float
- `category`: String (Predefined categories)
- `date`: Date

Categories:
- Food
- Travel
- Health
- Utilities
- Entertainment
- Other

## Development

The application uses:
- FastAPI for the backend
- SQLAlchemy for ORM
- Jinja2 for templating
- Bootstrap for styling
- SQLite for database

## License

MIT 