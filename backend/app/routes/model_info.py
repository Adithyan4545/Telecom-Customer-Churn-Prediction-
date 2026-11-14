"""Model information and feature importance endpoints."""

import json
from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.config import settings

router = APIRouter(prefix="/model", tags=["Model Information"])


@router.get("/info")
async def get_model_info():
    """Returns architecture, training specifications, and feature explanations for the active CatBoost pipeline."""
    return {
        "model_name": "CatBoost Classifier",
        "algorithm": "CatBoost Classifier (Optimized Telecom Churn Model)",
        "dataset_records": 7043,
        "features_count": 21,
        "pipeline_file": "experiments/accuracy_optimization/best_accuracy_pipeline.pkl",
        "decision_threshold": 0.50,
        "training_approach": "Nested Stratified 5-Fold Cross-Validation with Bayesian Hyperparameter Optimization",
        "preprocessing_steps": [
            "OptimizedTelecomFeatureEngineer: Synthesizes MonthlyChargeDiff, ServiceCount, and interaction features",
            "Numeric coercion of TotalCharges with 0.0 imputation for zero-tenure new customers",
            "Removal of customerID to prevent arbitrary identifier leakage",
            "StandardScaler normalization on continuous features (tenure, MonthlyCharges, TotalCharges, MonthlyChargeDiff)",
            "One-Hot Encoding with drop='first' on categorical features to prevent the dummy variable trap",
            "Strict pipeline isolation ensuring zero validation/test fold leakage",
        ],
        "feature_engineering_techniques": [
            "MonthlyChargeDiff: Residual charge variance capturing recent bill shock",
            "AutomaticPayment: Binary indicator for automated bank/card payments vs electronic checks",
            "FiberWithoutTechSupport: High-risk interaction group identifier (fiber customers without support)",
            "FamilyAnchor: Multi-user household indicator (Partner or Dependents)",
            "SecuritySupportCount: Count of cybersecurity and technical assistance add-ons",
            "ServiceCount: Total count of active telecommunication and digital services (1 to 9)",
        ],
    }


@router.get("/metrics")
async def get_model_metrics():
    """Returns verified model evaluation statistics for CatBoost Classifier."""
    return {
        "models": [
            {
                "name": "CatBoost Classifier",
                "strategy": "Fixed Default Threshold (0.50)",
                "accuracy": 80.36,
                "precision": 66.91,
                "recall": 51.47,
                "f1_score": 0.5817,
                "roc_auc": 0.8476,
                "pr_auc": 0.6631,
                "note": "Nested Stratified 5-Fold Cross-Validation result at default 0.50 threshold.",
                "confusion_matrix": {
                    "true_negatives": 4698,
                    "false_positives": 476,
                    "false_negatives": 907,
                    "true_positives": 962,
                },
            }
        ]
    }


@router.get("/feature-importance")
async def get_feature_importance():
    """Returns top 15 features and their domain descriptions."""
    return [
        {
            "feature": "tenure",
            "display_name": "Customer Tenure",
            "importance": 0.0618,
            "description": "Months customer has been with the provider. Recent subscribers (<12 mo) have the highest hazard rate.",
        },
        {
            "feature": "Contract_Two year",
            "display_name": "Two-Year Contract",
            "importance": 0.0206,
            "description": "Strongest contractual retention mechanism; churn rate drops to below 3%.",
        },
        {
            "feature": "TotalCharges",
            "display_name": "Total Lifetime Charges",
            "importance": 0.0127,
            "description": "Cumulative financial commitment; higher lifetime spend signals higher customer switching costs.",
        },
        {
            "feature": "MonthlyCharges",
            "display_name": "Monthly Charges ($)",
            "importance": 0.0085,
            "description": "Direct price elasticity driver; customers paying over $80/month are much more likely to compare competitors.",
        },
        {
            "feature": "Contract_One year",
            "display_name": "One-Year Contract",
            "importance": 0.0079,
            "description": "Mid-tier contract commitment; reduces churn to ~11% vs 42.7% for month-to-month.",
        },
        {
            "feature": "InternetService_Fiber optic",
            "display_name": "Fiber Optic Internet",
            "importance": 0.0069,
            "description": "Fiber customers exhibit higher attrition due to higher price expectations and sensitivity to connection drops.",
        },
        {
            "feature": "FiberWithoutTechSupport",
            "display_name": "Fiber Without Tech Support",
            "importance": 0.0063,
            "description": "Identifies unassisted fiber customers who experience connection friction and defect (~49% churn rate).",
        },
        {
            "feature": "StreamingCount",
            "display_name": "Streaming Services Count",
            "importance": 0.0051,
            "description": "Total TV and movie entertainment add-ons; higher engagement correlates with longer subscription life.",
        },
        {
            "feature": "MonthlyChargeDiff",
            "display_name": "Recent Bill Shock (Diff)",
            "importance": 0.0050,
            "description": "Difference between current rate and historical average; sudden increases trigger customer churn.",
        },
        {
            "feature": "PaymentMethod_Electronic check",
            "display_name": "Electronic Check Payment",
            "importance": 0.0044,
            "description": "Manual electronic check payments correlate with high defection rates (~45%) vs automated credit card billing.",
        },
        {
            "feature": "OnlineSecurity_No",
            "display_name": "No Online Security",
            "importance": 0.0039,
            "description": "Customers without cybersecurity protection view service as a commodity.",
        },
        {
            "feature": "TechSupport_No",
            "display_name": "No Tech Support",
            "importance": 0.0035,
            "description": "Customers lacking access to technical assistance defect rapidly when issues occur.",
        },
        {
            "feature": "AutomaticPayment",
            "display_name": "Automatic Payment Setup",
            "importance": 0.0031,
            "description": "Bank transfer or credit card auto-pay creates passive retention and minimal billing friction.",
        },
        {
            "feature": "PaperlessBilling_Yes",
            "display_name": "Paperless Billing",
            "importance": 0.0028,
            "description": "Correlates with price-conscious, digitally active customers who actively monitor their expenses.",
        },
        {
            "feature": "SecuritySupportCount",
            "display_name": "Security & Support Bundle",
            "importance": 0.0025,
            "description": "Total security services bundled; each additional service significantly decreases churn risk.",
        },
    ]
