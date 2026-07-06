"""
Anomaly / suspicious transaction detection.

Approach: use scikit-learn's IsolationForest, trained per spending category
(since a normal grocery transaction and a normal rent transaction have very
different typical amounts). A transaction is flagged if the model considers
its amount an outlier relative to the user's own historical amounts in that
category. Categories with fewer than 4 transactions are skipped (too little
data to judge what's "normal").
"""
from collections import defaultdict
import numpy as np
from sklearn.ensemble import IsolationForest


def detect_anomalies(transactions):
    """
    transactions: list of Transaction ORM objects (expenses only should be passed in
                  ideally, but this filters internally too)
    Returns: list of dicts: {"transaction": tx, "reason": str}
    """
    by_category = defaultdict(list)
    for t in transactions:
        type_val = getattr(t.type, "value", t.type)
        if type_val == "expense":
            by_category[t.category].append(t)

    flagged = []

    for category, txs in by_category.items():
        if len(txs) < 4:
            continue

        amounts = np.array([[t.amount] for t in txs])
        model = IsolationForest(contamination=0.15, random_state=42)
        preds = model.fit_predict(amounts)  # -1 = anomaly, 1 = normal

        mean_amt = amounts.mean()
        for tx, pred in zip(txs, preds):
            if pred == -1:
                direction = "higher" if tx.amount > mean_amt else "lower"
                flagged.append(
                    {
                        "transaction": tx,
                        "reason": (
                            f"This '{category}' transaction of {tx.amount:.2f} is "
                            f"unusually {direction} compared to your typical "
                            f"'{category}' spending (avg {mean_amt:.2f})."
                        ),
                    }
                )

    flagged.sort(key=lambda x: x["transaction"].date, reverse=True)
    return flagged
