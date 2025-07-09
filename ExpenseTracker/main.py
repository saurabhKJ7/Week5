from fastapi import FastAPI, Depends, HTTPException, Request, status, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List
from babel.numbers import format_currency
import models
import schemas
from database import engine, get_db, SessionLocal
import os

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker")

if not os.path.exists("templates"):
    os.makedirs("templates")

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def format_amount(amount: float) -> str:
    return format_currency(float(amount), 'INR', locale='en_IN')

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).all()
    total = sum(float(expense.amount) for expense in expenses)
    
    breakdown = {}
    for category in schemas.Category:
        cat_expenses = [e for e in expenses if e.category == category.value]
        breakdown[category.value] = sum(float(e.amount) for e in cat_expenses)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "expenses": expenses,
            "total": format_amount(total),
            "breakdown": {k: format_amount(v) for k, v in breakdown.items()},
            "categories": [c.value for c in schemas.Category],
            "format_amount": format_amount
        }
    )

@app.get("/expenses", response_model=List[schemas.Expense])
def get_expenses(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Expense)
    if start_date:
        query = query.filter(models.Expense.date >= start_date)
    if end_date:
        query = query.filter(models.Expense.date <= end_date)
    return query.all()

@app.post("/expenses", response_model=schemas.Expense, status_code=status.HTTP_201_CREATED)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = models.Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.put("/expenses/{expense_id}", response_model=schemas.Expense)
def update_expense(expense_id: int, expense: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if db_expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    update_data = expense.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_expense, key, value)
    
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if db_expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(db_expense)
    db.commit()
    return None

@app.get("/expenses/category/{category}", response_model=List[schemas.Expense])
def get_expenses_by_category(category: schemas.Category, db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).filter(models.Expense.category == category).all()
    return expenses

@app.get("/expenses/total", response_model=schemas.ExpenseTotal)
def get_total_expenses(db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).all()
    total = sum(float(expense.amount) for expense in expenses)
    
    breakdown = {}
    for category in schemas.Category:
        cat_expenses = [e for e in expenses if e.category == category.value]
        breakdown[category.value] = sum(float(e.amount) for e in cat_expenses)
    
    return {"total_amount": total, "breakdown": breakdown}

# Add sample data if the database is empty
def add_sample_data(db: Session):
    count = db.query(models.Expense).count()
    if count == 0:
        sample_expenses = [
            {
                "title": "Groceries",
                "amount": 2500.50,
                "category": "Food",
                "date": date(2024, 2, 1)
            },
            {
                "title": "Movie tickets",
                "amount": 800.00,
                "category": "Entertainment",
                "date": date(2024, 2, 2)
            },
            {
                "title": "Electricity bill",
                "amount": 3000.00,
                "category": "Utilities",
                "date": date(2024, 2, 3)
            }
        ]
        
        for expense_data in sample_expenses:
            expense = models.Expense(**expense_data)
            db.add(expense)
        db.commit()

# Add sample data on startup
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        add_sample_data(db)
    finally:
        db.close() 