"""Evaluation and inference diagnostic script for Telecom Customer Churn Prediction.

Loads the saved model pipeline and metadata, verifies performance on the test set,
provides threshold analysis, and tests single/batch sample inference.
"""

import json
import os
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

# Add parent directory to path to enable module imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.feature_engineering import TelecomFeatureEngineer

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "dataset" / "Telco-Customer-Churn.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "best_churn_model.pkl"
METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"


def run_evaluation():
    print("=" * 75)
    print(" TELECOM CUSTOMER CHURN PREDICTION - MODEL EVALUATION & INFERENCE TEST")
    print("=" * 75)

    # 1. Check Artifacts
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Run src/train_model.py first.")

    print(f"\n[1] Loading Saved Pipeline from: {MODEL_PATH.resolve()}")
    pipeline = joblib.load(MODEL_PATH)
    print("    Pipeline loaded successfully.")

    if METADATA_PATH.exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"    Active Model:    {metadata.get('model_name')}")
        print(f"    Imbalance Mode:  {metadata.get('strategy')}")
        print(f"    Train Samples:   {metadata.get('train_samples'):,}")
        print(f"    Test Samples:    {metadata.get('test_samples'):,}")

    # 2. Load Dataset and Recreate Stratified Test Split
    print(f"\n[2] Loading Evaluation Test Set from: {DATA_PATH.resolve()}")
    df = pd.read_csv(DATA_PATH)
    X = df.drop(columns=["Churn"])
    y = (df["Churn"].str.strip() == "Yes").astype(int)

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"    Test Set Size: {len(X_test):,} records (Retained: {(y_test == 0).sum():,}, Churned: {(y_test == 1).sum():,})")

    # 3. Model Inference on Test Set
    print("\n[3] Generating Test Set Predictions...")
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else None

    acc = accuracy_score(y_test, y_pred)
    b_acc = balanced_accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob) if y_prob is not None else float("nan")
    pr_auc = average_precision_score(y_test, y_prob) if y_prob is not None else float("nan")

    print("\n" + "-" * 55)
    print(" TEST SET PERFORMANCE METRICS SUMMARY")
    print("-" * 55)
    print(f" Accuracy:          {acc:.4f} ({acc*100:.2f}%)")
    print(f" Balanced Accuracy: {b_acc:.4f} ({b_acc*100:.2f}%)")
    print(f" Precision (Churn): {prec:.4f} ({prec*100:.2f}%)")
    print(f" Recall (Churn):    {rec:.4f} ({rec*100:.2f}%)")
    print(f" F1-Score (Churn):  {f1:.4f}")
    print(f" ROC-AUC:           {roc_auc:.4f}")
    print(f" PR-AUC:            {pr_auc:.4f}")
    print("-" * 55)

    # 4. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print("\n[4] Confusion Matrix Breakdown:")
    print(f"    True Negatives (Correctly Retained):  {tn:,}")
    print(f"    False Positives (Falsely Flagged):   {fp:,}")
    print(f"    False Negatives (Missed Churners):   {fn:,}")
    print(f"    True Positives (Correctly Churned):   {tp:,}")

    # 5. Classification Report
    print("\n[5] Detailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Retained (No)", "Churned (Yes)"], digits=4))

    # 6. Decision Threshold Sensitivity Analysis
    if y_prob is not None:
        print("[6] Decision Threshold Sensitivity Analysis:")
        print("    Threshold | Accuracy | Precision | Recall | F1-Score")
        print("    " + "-" * 50)
        for thresh in [0.30, 0.40, 0.50, 0.60, 0.70]:
            t_pred = (y_prob >= thresh).astype(int)
            t_acc = accuracy_score(y_test, t_pred)
            t_prec = precision_score(y_test, t_pred, zero_division=0)
            t_rec = recall_score(y_test, t_pred, zero_division=0)
            t_f1 = f1_score(y_test, t_pred, zero_division=0)
            print(f"      {thresh:.2f}    |  {t_acc:.4f}  |   {t_prec:.4f}  | {t_rec:.4f} |  {t_f1:.4f}")

    # 7. Single Customer Inference Sanity Check (Production Simulation)
    print("\n[7] Single Customer Inference Test (Simulating FastAPI JSON Payload):")
    sample_customer = {
        "customerID": "9999-PRODTEST",
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "No",
        "Dependents": "No",
        "tenure": 2,
        "PhoneService": "Yes",
        "MultipleLines": "No",
        "InternetService": "Fiber optic",
        "OnlineSecurity": "No",
        "OnlineBackup": "No",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "Yes",
        "StreamingMovies": "Yes",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 85.50,
        "TotalCharges": "171.00",
    }
    input_df = pd.DataFrame([sample_customer])
    pred_class = pipeline.predict(input_df)[0]
    pred_prob = pipeline.predict_proba(input_df)[0][1]

    print(f"    Customer Contract: {sample_customer['Contract']}, Tenure: {sample_customer['tenure']} mo, Monthly: ${sample_customer['MonthlyCharges']}")
    print(f"    Predicted Status:  {'CHURN RISK' if pred_class == 1 else 'RETAINED'}")
    print(f"    Churn Probability: {pred_prob:.2%}")
    print("\n" + "=" * 75)
    print(" EVALUATION COMPLETED SUCCESSFULLY")
    print("=" * 75)


if __name__ == "__main__":
    run_evaluation()
