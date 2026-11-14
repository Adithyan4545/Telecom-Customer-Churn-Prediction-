"""Customer management endpoints with search, filtering, and pagination."""

import math
from typing import Optional, List
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from backend.app.config import settings
from backend.app.schemas.customer import CustomerListItem, CustomerPaginationResponse, CustomerDetailResponse

router = APIRouter(prefix="/customers", tags=["Customers"])

# In-memory dataframe cache for fast querying
_df_cache = None


def get_customers_df() -> pd.DataFrame:
    global _df_cache
    if _df_cache is None:
        if settings.DATASET_PATH.exists():
            df = pd.read_csv(settings.DATASET_PATH)
            df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0.0)
            _df_cache = df
        else:
            _df_cache = pd.DataFrame()
    return _df_cache


@router.get("", response_model=CustomerPaginationResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by customer ID"),
    contract: Optional[str] = Query(None, description="Filter by Contract type"),
    churn: Optional[str] = Query(None, description="Filter by Actual Churn (Yes/No)"),
    sort_by: Optional[str] = Query("tenure", description="Column to sort by"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
):
    """Returns paginated, searchable, and filterable customer records from dataset."""
    df = get_customers_df()
    if df.empty:
        return CustomerPaginationResponse(items=[], total=0, page=page, page_size=page_size, total_pages=1)

    filtered_df = df

    # Search filter
    if search and search.strip():
        term = search.strip().lower()
        filtered_df = filtered_df[filtered_df["customerID"].str.lower().str.contains(term)]

    # Contract filter
    if contract and contract.strip() and contract != "All":
        filtered_df = filtered_df[filtered_df["Contract"] == contract.strip()]

    # Churn filter
    if churn and churn.strip() and churn != "All":
        filtered_df = filtered_df[filtered_df["Churn"] == churn.strip()]

    # Sorting
    valid_sort_cols = {
        "customer_id": "customerID",
        "gender": "gender",
        "tenure": "tenure",
        "Contract": "Contract",
        "MonthlyCharges": "MonthlyCharges",
        "TotalCharges": "TotalCharges",
        "actual_churn": "Churn",
    }
    col = valid_sort_cols.get(sort_by, "tenure")
    ascending = sort_order.lower() == "asc"
    filtered_df = filtered_df.sort_values(by=col, ascending=ascending)

    total = len(filtered_df)
    total_pages = max(1, math.ceil(total / page_size))
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    slice_df = filtered_df.iloc[start_idx:end_idx]

    items = []
    for idx, row in slice_df.iterrows():
        items.append(
            CustomerListItem(
                id=str(row.get("customerID", f"cust-{idx}")),
                customer_id=str(row.get("customerID", f"cust-{idx}")),
                gender=str(row.get("gender", "")),
                SeniorCitizen=int(row.get("SeniorCitizen", 0)),
                tenure=int(row.get("tenure", 0)),
                Contract=str(row.get("Contract", "")),
                PaymentMethod=str(row.get("PaymentMethod", "")),
                InternetService=str(row.get("InternetService", "")),
                MonthlyCharges=float(row.get("MonthlyCharges", 0.0)),
                TotalCharges=float(row.get("TotalCharges", 0.0)),
                actual_churn=str(row.get("Churn", "")),
            )
        )

    return CustomerPaginationResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer_details(customer_id: str):
    """Retrieves full attributes and history for a specific customer."""
    df = get_customers_df()
    match = df[df["customerID"].str.lower() == customer_id.strip().lower()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")

    row = match.iloc[0].to_dict()
    actual_churn = row.pop("Churn", None)

    return CustomerDetailResponse(
        customer_id=customer_id,
        actual_churn=actual_churn,
        customer_data=row,
    )
