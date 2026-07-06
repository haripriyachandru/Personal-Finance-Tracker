"""
Expense prediction model.

Approach: aggregate the user's historical expenses by month, then fit a
simple linear regression (scikit-learn) of monthly total expense vs. time
(month index) to project next month's expense. This is intentionally simple
and explainable, which is appropriate for a personal finance tool where
users should be able to trust/understand the prediction.

If there isn't enough history (< 2 months of data), we fall back to using
the average of whatever data is available.
"""
from collections import defaultdict
import numpy as np
from sklearn.linear_model import LinearRegression


def predict_next_month_expense(transactions):
    """
    transactions: list of objects with .type ("income"/"expense"), .amount, .date
    Returns: (predicted_value: float, trend: str, note: str)
    """
    monthly = defaultdict(float)
    for t in transactions:
        if str(t.type) in ("expense", "TransactionType.expense") or getattr(t.type, "value", t.type) == "expense":
            key = t.date.strftime("%Y-%m")
            monthly[key] += t.amount

    months_sorted = sorted(monthly.keys())

    if len(months_sorted) == 0:
        return 0.0, "no_data", "Not enough transaction history to make a prediction yet."

    if len(months_sorted) == 1:
        val = monthly[months_sorted[0]]
        return round(val, 2), "insufficient_history", (
            "Only one month of data is available, so this is simply last month's "
            "total. Add more months of data for a real trend-based prediction."
        )

    X = np.arange(len(months_sorted)).reshape(-1, 1)
    y = np.array([monthly[m] for m in months_sorted])

    model = LinearRegression()
    model.fit(X, y)

    next_index = np.array([[len(months_sorted)]])
    prediction = float(model.predict(next_index)[0])
    prediction = max(prediction, 0.0)

    slope = model.coef_[0]
    if slope > 1:
        trend = "increasing"
    elif slope < -1:
        trend = "decreasing"
    else:
        trend = "stable"

    note = (
        f"Based on linear regression over {len(months_sorted)} months of spending history."
    )

    return round(prediction, 2), trend, note
