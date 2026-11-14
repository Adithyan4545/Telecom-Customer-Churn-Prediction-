"""Customer management and pagination schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class CustomerListItem(BaseModel):
    """Row item in the customer management table."""
    id: str
    customer_id: str
    gender: str
    SeniorCitizen: int
    tenure: int
    Contract: str
    PaymentMethod: str
    InternetService: str
    MonthlyCharges: float
    TotalCharges: float
    actual_churn: Optional[str] = None  # "Yes" or "No"


class CustomerPaginationResponse(BaseModel):
    """Paginated customer table response."""
    items: List[CustomerListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class CustomerDetailResponse(BaseModel):
    """Full detail view for a specific customer."""
    customer_id: str
    actual_churn: Optional[str] = None
    customer_data: Dict[str, Any]
