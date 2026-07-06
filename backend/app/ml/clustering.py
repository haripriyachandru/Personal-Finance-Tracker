"""
User spending-behavior classification: Saver / Balanced / Overspender.

Approach: compute the user's savings rate for each month
  savings_rate = (income - expense) / income
We then classify the most recent month using a KMeans model whose 3
centroids are anchored to sensible reference points for what "Overspender",
"Balanced", and "Saver" savings rates typically look like:
  Overspender ~ -10% (spending more than earning)
  Balanced    ~ +10% (modest savings)
  Saver       ~ +35% (strong savings)

The user's actual monthly data points are combined with these anchors before
fitting, so the boundaries still adapt to the user's own data distribution,
but the labels stay meaningful even with very few months of history (which a
plain unanchored KMeans would not guarantee, since with only 2-3 raw data
points every point tends to become its own trivial cluster).

If there's only one data point, we skip KMeans and use fixed thresholds.
"""
from collections import defaultdict
import numpy as np
from sklearn.cluster import KMeans


DESCRIPTIONS = {
    "Saver": "You consistently spend well within your income and save a healthy portion each month. Keep it up!",
    "Balanced": "You generally spend close to what you earn, with moderate savings. There's room to build a stronger savings buffer.",
    "Overspender": "Your expenses are frequently close to or exceeding your income. Consider reviewing high-spending categories.",
}

# Reference anchors: (label, typical savings rate for that behavior)
ANCHORS = [("Overspender", -0.10), ("Balanced", 0.10), ("Saver", 0.35)]


def _compute_monthly_savings_rates(transactions):
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)

    for t in transactions:
        type_val = getattr(t.type, "value", t.type)
        key = t.date.strftime("%Y-%m")
        if type_val == "income":
            monthly_income[key] += t.amount
        else:
            monthly_expense[key] += t.amount

    months = sorted(set(monthly_income.keys()) | set(monthly_expense.keys()))

    savings_rates = []
    for m in months:
        income = monthly_income.get(m, 0.0)
        expense = monthly_expense.get(m, 0.0)
        if income > 0:
            savings_rates.append((income - expense) / income)
        elif expense > 0:
            savings_rates.append(-1.0)  # spending with no income that month

    return savings_rates


def _threshold_label(rate: float) -> str:
    if rate >= 0.2:
        return "Saver"
    elif rate >= 0:
        return "Balanced"
    return "Overspender"


def classify_user_behavior(transactions):
    savings_rates = _compute_monthly_savings_rates(transactions)

    if len(savings_rates) == 0:
        return "Balanced", DESCRIPTIONS["Balanced"], 0.0

    overall_rate = float(np.mean(savings_rates))
    most_recent_rate = savings_rates[-1]

    # With only one data point, clustering isn't meaningful - use thresholds.
    if len(savings_rates) == 1:
        label = _threshold_label(most_recent_rate)
        return label, DESCRIPTIONS[label], round(overall_rate, 3)

    anchor_labels = [a[0] for a in ANCHORS]
    anchor_values = np.array([[a[1]] for a in ANCHORS])

    X_user = np.array(savings_rates).reshape(-1, 1)
    X_combined = np.vstack([X_user, anchor_values])

    model = KMeans(n_clusters=3, init=anchor_values, n_init=1, random_state=42)
    model.fit(X_combined)

    # Order the fitted centroids ascending and map them to Overspender/Balanced/Saver
    # in that same ascending order, so labels always stay semantically meaningful
    # regardless of how the centroids shifted while fitting to the user's data.
    center_order = np.argsort(model.cluster_centers_.flatten())
    cluster_to_label = {
        cluster_id: anchor_labels[rank] for rank, cluster_id in enumerate(center_order)
    }

    predicted_cluster = model.predict([[most_recent_rate]])[0]
    label = cluster_to_label[predicted_cluster]

    return label, DESCRIPTIONS[label], round(overall_rate, 3)
