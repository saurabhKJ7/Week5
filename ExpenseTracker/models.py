from sqlalchemy import Column, Integer, String, Float, Date, CheckConstraint
from database import Base
from datetime import date, datetime

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    date = Column(Date, nullable=False, default=date.today)

    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
        CheckConstraint(
            "category IN ('Food', 'Travel', 'Health', 'Utilities', 'Entertainment', 'Other')",
            name='check_valid_category'
        ),
    )

    def __init__(self, **kwargs):
        if 'date' in kwargs and isinstance(kwargs['date'], str):
            kwargs['date'] = datetime.strptime(kwargs['date'], '%Y-%m-%d').date()
        super().__init__(**kwargs) 