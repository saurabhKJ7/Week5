# FastAPI Task Manager

A simple task manager application built with FastAPI, featuring both a REST API and a web interface.

## Features

- Create, read, update, and delete tasks
- Mark tasks as complete/incomplete
- Clean and responsive web interface
- RESTful API endpoints
- In-memory storage (no database required)

## Requirements

- Python 3.7+
- FastAPI
- Uvicorn
- Jinja2
- python-multipart

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd TaskApi
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the server:
```bash
uvicorn main:app --reload
```

2. Open your browser and navigate to:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Endpoints

- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Create a new task
- `PUT /api/tasks/{task_id}` - Update a task
- `DELETE /api/tasks/{task_id}` - Delete a task

### Example API Usage

Create a task:
```bash
curl -X POST "http://localhost:8000/api/tasks" \
     -H "Content-Type: application/json" \
     -d '{"title": "My new task"}'
```

List all tasks:
```bash
curl "http://localhost:8000/api/tasks"
```

## Web Interface

The web interface is available at http://localhost:8000 and provides a user-friendly way to:
- View all tasks
- Add new tasks
- Mark tasks as complete/incomplete
- Delete tasks

## Project Structure

```
TaskApi/
├── main.py              # FastAPI application and routes
├── requirements.txt     # Project dependencies
├── static/
│   └── styles.css      # CSS styles
└── templates/
    └── index.html      # HTML template
``` 