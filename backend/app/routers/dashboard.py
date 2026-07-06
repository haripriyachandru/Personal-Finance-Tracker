"""
Dashboard summary endpoint: totals, category breakdown, monthly trend.
Powers the charts on the React dashboard page.
"""
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter()


@router.get("/summary", response_model=schemas.DashboardSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    txs = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .all()
    )

    total_income = sum(t.amount for t in txs if t.type == models.TransactionType.income)
    total_expense = sum(t.amount for t in txs if t.type == models.TransactionType.expense)

    category_totals = defaultdict(float)
    for t in txs:
        if t.type == models.TransactionType.expense:
            category_totals[t.category] += t.amount

    category_breakdown = [
        schemas.CategoryBreakdown(category=cat, total=round(total, 2))
        for cat, total in sorted(category_totals.items(), key=lambda x: -x[1])
    ]

    monthly = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for t in txs:
        key = t.date.strftime("%Y-%m")
        if t.type == models.TransactionType.income:
            monthly[key]["income"] += t.amount
        else:
            monthly[key]["expense"] += t.amount

    monthly_trend = [
        schemas.MonthlyTrend(
            month=month,
            income=round(vals["income"], 2),
            expense=round(vals["expense"], 2),
        )
        for month, vals in sorted(monthly.items())
    ]

    return schemas.DashboardSummary(
        total_income=round(total_income, 2),
        total_expense=round(total_expense, 2),
        net_savings=round(total_income - total_expense, 2),
        category_breakdown=category_breakdown,
        monthly_trend=monthly_trend,
    )
