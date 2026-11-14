"""Feature engineering transformers and utilities for Telecom Customer Churn Prediction."""

from typing import Optional, List
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class TelecomFeatureEngineer(BaseEstimator, TransformerMixin):
    """Custom scikit-learn transformer that executes domain feature engineering

    and data hygiene on Telco churn data.
    Ensures safe handling of zero-tenure records and transforms raw data
    into informative behavioral and financial signals.
    """

    def __init__(self):
        pass

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        """Fit method (stateless transformer)."""
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform raw input DataFrame into engineered feature representation."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        else:
            X = X.copy()

        # 1. Drop customerID if present
        if "customerID" in X.columns:
            X = X.drop(columns=["customerID"])

        # 2. TotalCharges numeric conversion & missing value imputation
        # Note: All records with missing TotalCharges correspond to tenure == 0 (new joiners).
        # Imputing 0.0 reflects that they have not accrued any billing cycles yet.
        if "TotalCharges" in X.columns:
            X["TotalCharges"] = pd.to_numeric(X["TotalCharges"], errors="coerce").fillna(0.0)

        # 3. AverageMonthlySpend = TotalCharges / tenure (safe division for tenure == 0)
        if "tenure" in X.columns and "TotalCharges" in X.columns and "MonthlyCharges" in X.columns:
            X["AverageMonthlySpend"] = np.where(
                X["tenure"] > 0,
                X["TotalCharges"] / X["tenure"],
                X["MonthlyCharges"]
            )

        # 4. TenureGroup: New (0-12 months), Medium (13-36 months), Long-term (>36 months)
        if "tenure" in X.columns:
            X["TenureGroup"] = pd.cut(
                X["tenure"],
                bins=[-1, 12, 36, 150],
                labels=["New", "Medium", "Long-term"]
            ).astype(str)

        # 5. ServiceCount: Total services active for the customer
        services = [
            "PhoneService", "MultipleLines", "OnlineSecurity", "OnlineBackup",
            "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"
        ]
        existing_services = [s for s in services if s in X.columns]
        service_count = (X[existing_services] == "Yes").sum(axis=1)
        if "InternetService" in X.columns:
            service_count += (X["InternetService"].isin(["DSL", "Fiber optic"])).astype(int)
        X["ServiceCount"] = service_count

        # 6. SecuritySupportCount: Total cybersecurity and support add-ons
        sec_cols = [c for c in ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport"] if c in X.columns]
        X["SecuritySupportCount"] = (X[sec_cols] == "Yes").sum(axis=1)

        # 7. StreamingCount: Streaming entertainment add-ons
        stream_cols = [c for c in ["StreamingTV", "StreamingMovies"] if c in X.columns]
        X["StreamingCount"] = (X[stream_cols] == "Yes").sum(axis=1)

        # 8. ContractPeriod_Months: Numeric duration of contract commitment
        if "Contract" in X.columns:
            contract_map = {"Month-to-month": 1, "One year": 12, "Two year": 24}
            X["ContractPeriod_Months"] = X["Contract"].map(contract_map).fillna(1).astype(float)

        # 9. MonthlyChargeDiff: Difference between current monthly charge and historical average spend
        if "MonthlyCharges" in X.columns and "AverageMonthlySpend" in X.columns:
            X["MonthlyChargeDiff"] = X["MonthlyCharges"] - X["AverageMonthlySpend"]

        return X


def get_feature_column_types(transformed_df: pd.DataFrame):
    """Categorize columns into numeric and categorical for ColumnTransformer."""
    num_cols = [
        "tenure", "MonthlyCharges", "TotalCharges", "AverageMonthlySpend",
        "ServiceCount", "SecuritySupportCount", "StreamingCount",
        "ContractPeriod_Months", "MonthlyChargeDiff"
    ]
    # Filter to existing
    num_cols = [c for c in num_cols if c in transformed_df.columns]
    cat_cols = [c for c in transformed_df.columns if c not in num_cols]
    return num_cols, cat_cols
