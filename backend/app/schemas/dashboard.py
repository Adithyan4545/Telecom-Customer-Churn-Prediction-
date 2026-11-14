"""Dashboard KPI and summary visualization schemas."""

from typing import List, Dict, Any
from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    """Top-level metrics for dashboard cards."""
    total_customers: int
    churned_customers: int
    active_customers: int
    churn_rate: float
    total_predictions: int
    high_risk_predictions: int


class PieChartItem(BaseModel):
    name: str
    value: int
    percentage: float
    color: str


class MonthlyChargesDistItem(BaseModel):
    range: str
    total_count: int
    churn_count: int
    churn_rate: float


class ContractChurnItem(BaseModel):
    contract: str
    retained: int
    churned: int
    churn_rate: float


class TenureGroupItem(BaseModel):
    tenure_group: str
    retained: int
    churned: int
    churn_rate: float


class PaymentMethodItem(BaseModel):
    payment_method: str
    retained: int
    churned: int
    churn_rate: float


class MonthlyTrendItem(BaseModel):
    month: str
    predictions_count: int
    churn_count: int
    retention_count: int
