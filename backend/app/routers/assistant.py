"""
AI Assistant endpoint: generates natural-language financial insights.

By default this uses a built-in rule-based insight generator (no external
API key needed, works fully offline). If the user sets ANTHROPIC_API_KEY in
backend/.env, it will instead call Claude to turn the same computed stats
into more natural, conversational insights.
"""
import os
import json
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user
from ..ml.predictor import predict_next_month_expense
from ..ml.clustering import classify_user_behavior
from .dashboard import get_summary as _get_summary_impl

load_dotenv()

router = APIRouter()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()


def _rule_based_insights(summary: schemas.DashboardSummary, prediction, cluster_label, cluster_desc) -> List[str]:
    insights = []

    if summary.total_income > 0:
        savings_pct = (summary.net_savings / summary.total_income) * 100
        if savings_pct < 0:
            insights.append(
                f"You're spending more than you earn overall (net {summary.net_savings:.2f}). "
                "It may help to review your largest expense categories."
            )
        else:
            insights.append(
                f"You're saving about {savings_pct:.1f}% of your income overall — "
                f"a net of {summary.net_savings:.2f}."
            )

    if summary.category_breakdown:
        top = summary.category_breakdown[0]
        insights.append(
            f"Your highest spending category is '{top.category}' at {top.total:.2f}. "
            "Consider setting a monthly budget cap for this category."
        )
        if len(summary.category_breakdown) > 1:
            second = summary.category_breakdown[1]
            insights.append(
                f"'{second.category}' is your second biggest expense at {second.total:.2f}."
            )

    pred_val, trend, _ = prediction
    if trend == "increasing":
        insights.append(
            f"Your expenses are trending upward — next month is projected at "
            f"around {pred_val:.2f}. Consider tightening discretionary spending."
        )
    elif trend == "decreasing":
        insights.append(
            f"Good news — your expenses are trending down, projected around "
            f"{pred_val:.2f} next month."
        )
    elif trend == "stable":
        insights.append(
            f"Your monthly expenses look fairly stable, projected around {pred_val:.2f} next month."
        )

    insights.append(f"Based on your recent activity, you're currently classified as a '{cluster_label}': {cluster_desc}")

    if not insights:
        insights.append("Add some income and expense transactions to start receiving personalized insights.")

    return insights


def _call_claude_for_insights(stats: dict) -> List[str]:
    """
    Optional: calls Anthropic's Claude API to generate richer natural-language
    insights from the same computed financial statistics. Requires the
    `anthropic` package (add `anthropic` to requirements.txt if you enable this)
    and ANTHROPIC_API_KEY set in backend/.env
    """
    import anthropic  # imported lazily so it's only required if this path is used

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are a helpful personal finance assistant. Based on the following
JSON summary of a user's finances, write 3-5 short, friendly, actionable insights
(each 1-2 sentences). Respond ONLY with a JSON array of strings, nothing else.

Financial data:
{json.dumps(stats, indent=2)}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    text = text.strip().strip("```json").strip("```").strip()

    try:
        insights = json.loads(text)
        if isinstance(insights, list):
            return [str(i) for i in insights]
    except Exception:
        pass

    return [text] if text else []


@router.get("/insights", response_model=schemas.InsightsOut)
def get_insights(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    summary = _get_summary_impl(db=db, current_user=current_user)

    txs = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.date)
        .all()
    )

    pred_val, trend, note = predict_next_month_expense(txs)
    cluster_label, cluster_desc, savings_rate = classify_user_behavior(txs)

    if ANTHROPIC_API_KEY:
        stats = {
            "total_income": summary.total_income,
            "total_expense": summary.total_expense,
            "net_savings": summary.net_savings,
            "category_breakdown": [c.model_dump() for c in summary.category_breakdown],
            "monthly_trend": [m.model_dump() for m in summary.monthly_trend],
            "predicted_next_month_expense": pred_val,
            "expense_trend": trend,
            "behavior_label": cluster_label,
            "savings_rate": savings_rate,
        }
        try:
            insights = _call_claude_for_insights(stats)
            if insights:
                return schemas.InsightsOut(insights=insights, source="ai")
        except Exception:
            # Fall back silently to rule-based insights if the API call fails
            pass

    insights = _rule_based_insights(summary, (pred_val, trend, note), cluster_label, cluster_desc)
    return schemas.InsightsOut(insights=insights, source="rule-based")
