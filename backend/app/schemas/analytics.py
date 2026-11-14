"""Analytics breakdown and model evaluation schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class MetricBreakdown(BaseModel):
    category: str
    total: int
    churned: int
    churn_rate: float


class ModelMetricsResponse(BaseModel):
    """Verified cross-validation model evaluation statistics."""
    model_name: str
    strategy: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    pr_auc: Optional[float] = None
    note: str
