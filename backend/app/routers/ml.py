"""
Machine Learning endpoints: expense prediction, anomaly detection,
and spending-behavior clustering.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user
from ..ml.predictor import predict_next_month_expense
from ..ml.anomaly import detect_anomalies
from ..ml.clustering import classify_user_behavior

router = APIRouter()


def _get_user_transactions(db: Session, user_id: int):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == user_id)
        .order_by(models.Transaction.date)
        .all()
    )


@router.get("/predict", response_model=schemas.PredictionOut)
def predict_expense(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    txs = _get_user_transactions(db, current_user.id)
    prediction, trend, note = predict_next_month_expense(txs)
    return schemas.PredictionOut(
        next_month_predicted_expense=prediction,
        trend=trend,
        confidence_note=note,
    )


@router.get("/anomalies", response_model=List[schemas.AnomalyOut])
def get_anomalies(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    txs = _get_user_transactions(db, current_user.id)
    flagged = detect_anomalies(txs)

    # Persist the flag on the transaction record for visibility elsewhere in the UI
    flagged_ids = {f["transaction"].id for f in flagged}
    for tx in txs:
        tx.is_anomaly = 1 if tx.id in flagged_ids else 0
    db.commit()

    return [
        schemas.AnomalyOut(
            transaction=schemas.TransactionOut.model_validate(f["transaction"]),
            reason=f["reason"],
        )
        for f in flagged
    ]


@router.get("/cluster", response_model=schemas.ClusterOut)
def get_cluster(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    txs = _get_user_transactions(db, current_user.id)
    label, description, savings_rate = classify_user_behavior(txs)
    return schemas.ClusterOut(
        label=label, description=description, savings_rate=savings_rate
    )
