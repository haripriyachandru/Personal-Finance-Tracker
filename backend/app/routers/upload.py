"""
CSV bank statement upload endpoint.

Expected CSV columns (case-insensitive, flexible order):
  date, description, category, amount, type

- "type" should be "income" or "expense". If missing, it is inferred:
  positive amount => income, negative amount => expense (and amount is
  stored as an absolute value).
- "category" is optional; defaults to "Other" if not provided.

Example CSV:
date,description,category,amount,type
2025-01-05,Salary,Salary,50000,income
2025-01-07,Groceries,Food,1200,expense
2025-01-10,Netflix,Entertainment,499,expense
"""
import io
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter()

REQUIRED_ANY = {"amount"}


def _parse_date(value):
    if pd.isna(value):
        return datetime.utcnow()
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return datetime.utcnow()


@router.post("/csv", response_model=schemas.UploadResult)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    df.columns = [c.strip().lower() for c in df.columns]

    if "amount" not in df.columns:
        raise HTTPException(
            status_code=400, detail="CSV must contain at least an 'amount' column"
        )

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():
        try:
            amount = float(row.get("amount"))
        except (TypeError, ValueError):
            skipped += 1
            continue

        tx_type = str(row.get("type", "")).strip().lower()
        if tx_type not in ("income", "expense"):
            tx_type = "income" if amount >= 0 else "expense"

        amount = abs(amount)
        category = str(row.get("category", "Other")).strip() or "Other"
        description = str(row.get("description", "")).strip() or None
        date_value = _parse_date(row.get("date"))

        tx = models.Transaction(
            user_id=current_user.id,
            type=tx_type,
            category=category,
            amount=amount,
            description=description,
            date=date_value,
        )
        db.add(tx)
        inserted += 1

    db.commit()

    return schemas.UploadResult(
        inserted=inserted,
        skipped=skipped,
        message=f"Successfully imported {inserted} transactions ({skipped} skipped).",
    )
