"""Prediction input, output, and history schemas."""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, field_validator


class CustomerFeatures(BaseModel):
    """Raw customer attributes required for feature engineering and inference."""
    gender: str = Field(..., description="Female or Male")
    SeniorCitizen: int = Field(..., ge=0, le=1, description="0 or 1")
    Partner: str = Field(..., description="Yes or No")
    Dependents: str = Field(..., description="Yes or No")
    tenure: int = Field(..., ge=0, le=100, description="Months subscribed (0 to 100)")
    PhoneService: str = Field(..., description="Yes or No")
    MultipleLines: str = Field(..., description="No, Yes, or No phone service")
    InternetService: str = Field(..., description="DSL, Fiber optic, or No")
    OnlineSecurity: str = Field(..., description="No, Yes, or No internet service")
    OnlineBackup: str = Field(..., description="No, Yes, or No internet service")
    DeviceProtection: str = Field(..., description="No, Yes, or No internet service")
    TechSupport: str = Field(..., description="No, Yes, or No internet service")
    StreamingTV: str = Field(..., description="No, Yes, or No internet service")
    StreamingMovies: str = Field(..., description="No, Yes, or No internet service")
    Contract: str = Field(..., description="Month-to-month, One year, or Two year")
    PaperlessBilling: str = Field(..., description="Yes or No")
    PaymentMethod: str = Field(
        ...,
        description="Electronic check, Mailed check, Bank transfer (automatic), Credit card (automatic)",
    )
    MonthlyCharges: float = Field(..., ge=0.0, description="Current monthly charge in dollars")
    TotalCharges: Union[float, str] = Field(..., description="Total cumulative charge in dollars or blank/0.0")

    @field_validator("TotalCharges")
    @classmethod
    def validate_total_charges(cls, v, values):
        """Ensures TotalCharges is valid float or blank string for zero tenure."""
        if isinstance(v, str):
            v_clean = v.strip()
            if v_clean == "":
                return 0.0
            try:
                val = float(v_clean)
                if val < 0.0:
                    raise ValueError("Total charges cannot be negative")
                return val
            except ValueError:
                raise ValueError("Total charges must be a valid non-negative number")
        elif isinstance(v, (int, float)):
            if v < 0.0:
                raise ValueError("Total charges cannot be negative")
            return float(v)
        return 0.0


class PredictionRequest(BaseModel):
    """Payload to request churn inference."""
    customer_id: Optional[str] = Field(None, description="Optional customer ID")
    features: CustomerFeatures
    model_name: Optional[str] = Field("CatBoost Classifier", description="Active model identifier")
    threshold: Optional[float] = Field(0.50, description="Fixed classification decision threshold")
    save_to_db: Optional[bool] = Field(False, description="Whether to automatically store this prediction")


class PredictionResponse(BaseModel):
    """Inference result returned to frontend."""
    prediction_id: Optional[str] = None
    customer_id: str
    predicted_class: int
    predicted_label: str  # "Churn" or "No Churn"
    churn_probability: float  # e.g. 0.785
    churn_percentage: float  # e.g. 78.5
    risk_level: str  # "High Risk", "Medium Risk", "Low Risk"
    model_name: str
    threshold: float
    recommended_action: str
    created_at: datetime


class SavePredictionRequest(BaseModel):
    """Payload to explicitly save a previously run prediction."""
    customer_id: str
    customer_features: Dict[str, Any]
    predicted_class: int
    churn_probability: float
    risk_level: str
    model_name: str
    threshold: float


class PredictionHistoryItem(BaseModel):
    """Prediction history record stored in database."""
    id: str
    _id: Optional[str] = None
    customer_id: str
    customer_features: Dict[str, Any]
    predicted_class: int
    predicted_label: str
    churn_probability: float
    churn_percentage: float
    risk_level: str
    model_name: str
    threshold: float
    created_at: datetime


class PredictionHistoryPagination(BaseModel):
    """Paginated list of saved predictions."""
    items: List[PredictionHistoryItem]
    predictions: Optional[List[PredictionHistoryItem]] = None
    total: int
    page: int
    page_size: int
    total_pages: int
    pages: Optional[int] = None
