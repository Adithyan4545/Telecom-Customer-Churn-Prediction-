"""Enhanced feature engineering transformers for Telecom Customer Churn Prediction.

Eliminates collinear features and introduces strong domain interaction signals:
- Drops customerID
- Imputes 0.0 for zero-tenure TotalCharges
- Removes high-collinearity pairs (AverageMonthlySpend, ContractPeriod_Months)
- Adds domain interactions: AutomaticPayment, FiberWithoutTechSupport, FamilyAnchor, SeniorAlone,
  SecuritySupportCount, ServiceCount, StreamingCount, MonthlyChargeDiff.
"""

from typing import Optional, List, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class OptimizedTelecomFeatureEngineer(BaseEstimator, TransformerMixin):
    """Refined scikit-learn compatible feature transformer designed to eliminate

    multicollinearity and create high-signal domain features for churn modeling.
    """

    def __init__(self):
        pass

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        else:
            X = X.copy()

        # 1. Drop customerID if present
        if "customerID" in X.columns:
            X = X.drop(columns=["customerID"])

        # 2. TotalCharges numeric conversion & zero-tenure imputation
        if "TotalCharges" in X.columns:
            X["TotalCharges"] = pd.to_numeric(X["TotalCharges"], errors="coerce").fillna(0.0)

        # 3. MonthlyChargeDiff: residual charge drift (uncorrelated with tenure/spend)
        if "MonthlyCharges" in X.columns and "TotalCharges" in X.columns and "tenure" in X.columns:
            avg_spend = np.where(X["tenure"] > 0, X["TotalCharges"] / X["tenure"], X["MonthlyCharges"])
            X["MonthlyChargeDiff"] = X["MonthlyCharges"] - avg_spend

        # 4. Domain Feature: AutomaticPayment (strong negative correlation with churn)
        if "PaymentMethod" in X.columns:
            X["AutomaticPayment"] = X["PaymentMethod"].str.contains("automatic", case=False, na=False).astype(int)

        # 5. Domain Feature: FiberWithoutTechSupport (highest hazard group ~49% churn rate)
        if "InternetService" in X.columns and "TechSupport" in X.columns:
            X["FiberWithoutTechSupport"] = (
                (X["InternetService"] == "Fiber optic") & (X["TechSupport"] == "No")
            ).astype(int)

        # 6. Domain Feature: FamilyAnchor (Partner or Dependents creates retention buffer)
        if "Partner" in X.columns and "Dependents" in X.columns:
            X["FamilyAnchor"] = ((X["Partner"] == "Yes") | (X["Dependents"] == "Yes")).astype(int)

        # 7. Domain Feature: SeniorAlone (unanchored senior citizen with higher attrition risk)
        if "SeniorCitizen" in X.columns and "Partner" in X.columns and "Dependents" in X.columns:
            X["SeniorAlone"] = (
                (X["SeniorCitizen"] == 1) & (X["Partner"] == "No") & (X["Dependents"] == "No")
            ).astype(int)

        # 8. Domain Feature: SecuritySupportCount (security add-on bundle count)
        sec_cols = [c for c in ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport"] if c in X.columns]
        X["SecuritySupportCount"] = (X[sec_cols] == "Yes").sum(axis=1)

        # 9. Domain Feature: ServiceCount (total active services)
        services = [
            "PhoneService", "MultipleLines", "OnlineSecurity", "OnlineBackup",
            "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"
        ]
        existing_services = [s for s in services if s in X.columns]
        service_count = (X[existing_services] == "Yes").sum(axis=1)
        if "InternetService" in X.columns:
            service_count += (X["InternetService"].isin(["DSL", "Fiber optic"])).astype(int)
        X["ServiceCount"] = service_count

        # 10. Domain Feature: StreamingCount (streaming bundle count)
        stream_cols = [c for c in ["StreamingTV", "StreamingMovies"] if c in X.columns]
        X["StreamingCount"] = (X[stream_cols] == "Yes").sum(axis=1)

        return X


def get_optimized_column_types(transformed_df: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    """Separates numerical, categorical, and binary indicator features."""
    num_cols = [
        "tenure", "MonthlyCharges", "TotalCharges", "SecuritySupportCount",
        "ServiceCount", "StreamingCount", "MonthlyChargeDiff"
    ]
    bin_cols = [
        "AutomaticPayment", "FiberWithoutTechSupport", "FamilyAnchor", "SeniorAlone"
    ]
    num_cols = [c for c in num_cols if c in transformed_df.columns]
    bin_cols = [c for c in bin_cols if c in transformed_df.columns]
    cat_cols = [c for c in transformed_df.columns if c not in num_cols and c not in bin_cols]
    return num_cols, cat_cols, bin_cols
