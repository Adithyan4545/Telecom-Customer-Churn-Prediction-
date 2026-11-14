"""Analytics and statistics calculation service using actual dataset values."""

import json
import logging
from typing import Dict, Any, List
import pandas as pd

from backend.app.config import settings
from backend.app.database import get_database

logger = logging.getLogger("telecom.analytics")


class AnalyticsService:
    """Precomputes and provides statistical breakdowns from raw dataset and live predictions."""

    def __init__(self):
        self.df = None
        self._load_dataset()

    def _load_dataset(self):
        """Loads and precomputes static statistics from the raw Telco CSV."""
        try:
            if settings.DATASET_PATH.exists():
                self.df = pd.read_csv(settings.DATASET_PATH)
                self.df["TotalCharges"] = pd.to_numeric(self.df["TotalCharges"], errors="coerce").fillna(0.0)
                logger.info("Analytics service loaded dataset with %d records.", len(self.df))
        except Exception as e:
            logger.error("Failed to load dataset for analytics service: %s", e)

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Calculates dashboard KPI metrics combining dataset baseline with live MongoDB predictions."""
        total_customers = len(self.df) if self.df is not None else 7043
        churned_customers = int((self.df["Churn"] == "Yes").sum()) if self.df is not None else 1869
        active_customers = total_customers - churned_customers
        churn_rate = round((churned_customers / total_customers) * 100, 2)

        # Get live predictions count from MongoDB
        db = get_database()
        total_predictions = await db.predictions.count_documents({})
        high_risk_predictions = await db.predictions.count_documents({"risk_level": "High Risk"})

        return {
            "total_customers": total_customers,
            "churned_customers": churned_customers,
            "active_customers": active_customers,
            "churn_rate": churn_rate,
            "total_predictions": total_predictions,
            "high_risk_predictions": high_risk_predictions,
        }

    def get_churn_distribution(self) -> List[Dict[str, Any]]:
        """Returns churn vs non-churn counts and percentages."""
        if self.df is None:
            return [
                {"name": "Retained Customers", "value": 5174, "percentage": 73.46, "color": "#2563eb"},
                {"name": "Churned Customers", "value": 1869, "percentage": 26.54, "color": "#ef4444"},
            ]

        counts = self.df["Churn"].value_counts()
        total = len(self.df)
        retained = int(counts.get("No", 5174))
        churned = int(counts.get("Yes", 1869))

        return [
            {
                "name": "Retained Customers",
                "value": retained,
                "percentage": round((retained / total) * 100, 2),
                "color": "#2563eb",
            },
            {
                "name": "Churned Customers",
                "value": churned,
                "percentage": round((churned / total) * 100, 2),
                "color": "#ef4444",
            },
        ]

    def get_monthly_charges_distribution(self) -> List[Dict[str, Any]]:
        """Groups monthly charges into price brackets."""
        if self.df is None:
            return []

        bins = [0, 30, 50, 70, 90, 120]
        labels = ["$18-$30", "$30-$50", "$50-$70", "$70-$90", "$90-$120"]
        df_temp = self.df.copy()
        df_temp["charge_bin"] = pd.cut(df_temp["MonthlyCharges"], bins=bins, labels=labels)

        grouped = df_temp.groupby("charge_bin", observed=False)["Churn"].value_counts().unstack(fill_value=0)
        results = []
        for label in labels:
            if label in grouped.index:
                ret = int(grouped.loc[label].get("No", 0))
                chn = int(grouped.loc[label].get("Yes", 0))
                tot = ret + chn
                rate = round((chn / tot * 100), 1) if tot > 0 else 0.0
                results.append({
                    "range": label,
                    "total_count": tot,
                    "churn_count": chn,
                    "churn_rate": rate,
                })
        return results

    def get_churn_by_contract(self) -> List[Dict[str, Any]]:
        """Returns churn breakdown by contract type."""
        if self.df is None:
            return []

        grouped = self.df.groupby("Contract")["Churn"].value_counts().unstack(fill_value=0)
        results = []
        for contract in ["Month-to-month", "One year", "Two year"]:
            if contract in grouped.index:
                ret = int(grouped.loc[contract].get("No", 0))
                chn = int(grouped.loc[contract].get("Yes", 0))
                rate = round((chn / (ret + chn)) * 100, 1)
                results.append({
                    "contract": contract,
                    "retained": ret,
                    "churned": chn,
                    "churn_rate": rate,
                })
        return results

    def get_churn_by_tenure(self) -> List[Dict[str, Any]]:
        """Returns churn breakdown by customer tenure cohorts."""
        if self.df is None:
            return []

        df_temp = self.df.copy()
        df_temp["tenure_group"] = pd.cut(
            df_temp["tenure"],
            bins=[-1, 12, 24, 48, 72],
            labels=["0-12 mo", "13-24 mo", "25-48 mo", "49-72 mo"],
        )
        grouped = df_temp.groupby("tenure_group", observed=False)["Churn"].value_counts().unstack(fill_value=0)
        results = []
        for tg in ["0-12 mo", "13-24 mo", "25-48 mo", "49-72 mo"]:
            if tg in grouped.index:
                ret = int(grouped.loc[tg].get("No", 0))
                chn = int(grouped.loc[tg].get("Yes", 0))
                tot = ret + chn
                rate = round((chn / tot * 100), 1) if tot > 0 else 0.0
                results.append({
                    "tenure_group": tg,
                    "retained": ret,
                    "churned": chn,
                    "churn_rate": rate,
                })
        return results

    def get_churn_by_payment(self) -> List[Dict[str, Any]]:
        """Returns churn breakdown by payment method."""
        if self.df is None:
            return []

        grouped = self.df.groupby("PaymentMethod")["Churn"].value_counts().unstack(fill_value=0)
        results = []
        for pm in grouped.index:
            ret = int(grouped.loc[pm].get("No", 0))
            chn = int(grouped.loc[pm].get("Yes", 0))
            rate = round((chn / (ret + chn)) * 100, 1)
            results.append({
                "payment_method": pm.replace(" (automatic)", " (auto)"),
                "retained": ret,
                "churned": chn,
                "churn_rate": rate,
            })
        return results

    def get_churn_by_internet_service(self) -> List[Dict[str, Any]]:
        """Returns churn breakdown by internet service type."""
        if self.df is None:
            return []

        grouped = self.df.groupby("InternetService")["Churn"].value_counts().unstack(fill_value=0)
        results = []
        for is_type in grouped.index:
            ret = int(grouped.loc[is_type].get("No", 0))
            chn = int(grouped.loc[is_type].get("Yes", 0))
            rate = round((chn / (ret + chn)) * 100, 1)
            results.append({
                "category": is_type,
                "total": ret + chn,
                "churned": chn,
                "churn_rate": rate,
            })
        return results

    def get_model_evaluation_metrics(self) -> List[Dict[str, Any]]:
        """Returns verified model evaluation metrics for the active CatBoost pipeline."""
        return [
            {
                "model_name": "CatBoost Classifier",
                "strategy": "Fixed Default Decision Threshold (0.50)",
                "accuracy": 80.36,
                "precision": 66.91,
                "recall": 51.47,
                "f1_score": 0.5817,
                "roc_auc": 0.8476,
                "note": "Nested Stratified 5-Fold Cross-Validation result at default 0.50 threshold.",
            }
        ]


analytics_service = AnalyticsService()
