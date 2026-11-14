"""Analytics endpoints for churn breakdown charts and model evaluation."""

from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/churn-by-contract")
async def get_churn_by_contract():
    """Returns churn breakdown by contract type."""
    return analytics_service.get_churn_by_contract()


@router.get("/churn-by-tenure")
async def get_churn_by_tenure():
    """Returns churn breakdown by tenure groups."""
    return analytics_service.get_churn_by_tenure()


@router.get("/churn-by-payment")
async def get_churn_by_payment():
    """Returns churn breakdown by payment method."""
    return analytics_service.get_churn_by_payment()


@router.get("/churn-by-internet")
async def get_churn_by_internet():
    """Returns churn breakdown by internet service type."""
    return analytics_service.get_churn_by_internet_service()


@router.get("/model-metrics")
async def get_model_evaluation_metrics():
    """Returns verified model evaluation metrics from cross-validation experiments."""
    return analytics_service.get_model_evaluation_metrics()
