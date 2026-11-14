"""Dashboard KPI and summary visualization endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.schemas.dashboard import DashboardStatsResponse
from backend.app.services.analytics_service import analytics_service
from backend.app.services.prediction_service import prediction_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats():
    """Returns top KPI cards."""
    return await analytics_service.get_dashboard_stats()


@router.get("/churn-distribution")
async def get_churn_distribution():
    """Returns churn vs non-churn counts and percentages."""
    return analytics_service.get_churn_distribution()


@router.get("/monthly-charges-distribution")
async def get_monthly_charges_distribution():
    """Returns monthly charges distribution across buckets."""
    return analytics_service.get_monthly_charges_distribution()


@router.get("/recent-predictions")
async def get_recent_predictions(limit: int = 5):
    """Returns most recent prediction records for the dashboard."""
    history = await prediction_service.get_prediction_history(page=1, page_size=limit)
    return history.items
