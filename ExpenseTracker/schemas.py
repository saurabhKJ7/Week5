from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import Optional, List, Dict
from enum import Enum

class Category(str, Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    HEALTH = "Health"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    OTHER = "Other"

class ExpenseBase(BaseModel):
    title: str
    amount: float = Field(gt=0)
    category: Category
    date: Optional[str] = None

    @validator('date')
    def validate_date(cls, v):
        if not v:
            return str(date.today())
        try:
            # Try to parse the date string
            parsed_date = datetime.strptime(v, '%Y-%m-%d').date()
            return str(parsed_date)
        except (ValueError, TypeError):
            raise ValueError('Invalid date format. Use YYYY-MM-DD')

class ExpenseCreate(ExpenseBase):
    pass

class Expense(BaseModel):
    id: int
    title: str
    amount: float
    category: Category
    date: date

    class Config:
        from_attributes = True

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[Category] = None
    date: Optional[str] = None

    @validator('date')
    def validate_optional_date(cls, v):
        if not v:
            return None
        try:
            datetime.strptime(v, '%Y-%m-%d').date()
            return v
        except (ValueError, TypeError):
            raise ValueError('Invalid date format. Use YYYY-MM-DD')

class ExpenseTotal(BaseModel):
    total_amount: float
    breakdown: Dict[str, float] 