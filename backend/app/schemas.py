"""
Pydantic schemas used for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from .models import TransactionType


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Transactions ----------
class TransactionCreate(BaseModel):
    type: TransactionType
    category: str
    amount: float = Field(gt=0)
    description: Optional[str] = None
    date: Optional[datetime] = None


class TransactionOut(BaseModel):
    id: int
    type: TransactionType
    category: str
    amount: float
    description: Optional[str]
    date: datetime
    is_anomaly: int

    class Config:
        from_attributes = True


class UploadResult(BaseModel):
    inserted: int
    skipped: int
    message: str


# ---------- Dashboard ----------
class CategoryBreakdown(BaseModel):
    category: str
    total: float


class MonthlyTrend(BaseModel):
    month: str
    income: float
    expense: float


class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    net_savings: float
    category_breakdown: List[CategoryBreakdown]
    monthly_trend: List[MonthlyTrend]


# ---------- ML ----------
class PredictionOut(BaseModel):
    next_month_predicted_expense: float
    trend: str
    confidence_note: str


class AnomalyOut(BaseModel):
    transaction: TransactionOut
    reason: str


class ClusterOut(BaseModel):
    label: str
    description: str
    savings_rate: float


class InsightsOut(BaseModel):
    insights: List[str]
    source: str  # "ai" or "rule-based"
