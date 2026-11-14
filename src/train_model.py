"""Training and model optimization pipeline for Telecom Customer Churn Prediction.

Executes data preprocessing, feature engineering, multi-algorithm training,
class imbalance handling, hyperparameter tuning, model evaluation,
and saves the final end-to-end deployable pipeline.
"""

import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, Any, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.base import BaseEstimator
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

# Add parent directory to path to enable module imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.feature_engineering import TelecomFeatureEngineer, get_feature_column_types

warnings.filterwarnings("ignore")

# Define project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "dataset" / "Telco-Customer-Churn.csv"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def load_and_split_data(
    data_path: Path = DATA_PATH, test_size: float = 0.2, random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Loads raw Telco CSV and performs an 80/20 stratified train-test split."""
    print(f"[1/8] Loading dataset from: {data_path.resolve()}")
    df = pd.read_csv(data_path)

    # Separate target
    target_col = "Churn"
    X = df.drop(columns=[target_col])
    y = (df[target_col].str.strip() == "Yes").astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    print(f"      Total records: {len(df):,}")
    print(f"      Train set:     {len(X_train):,} ({len(X_train)/len(df):.1%}) | Churn rate: {y_train.mean():.2%}")
    print(f"      Test set:      {len(X_test):,} ({len(X_test)/len(df):.1%}) | Churn rate: {y_test.mean():.2%}")
    return X_train, X_test, y_train, y_test


def build_preprocessor(X_train_sample: pd.DataFrame) -> Tuple[ColumnTransformer, list, list]:
    """Constructs the ColumnTransformer for numeric scaling and categorical one-hot encoding."""
    fe = TelecomFeatureEngineer()
    X_fe = fe.transform(X_train_sample)
    num_cols, cat_cols = get_feature_column_types(X_fe)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), cat_cols),
        ]
    )
    return preprocessor, num_cols, cat_cols


def evaluate_predictions(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray = None) -> Dict[str, float]:
    """Calculates all key classification performance metrics."""
    metrics = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Balanced_Accuracy": balanced_accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1_Score": f1_score(y_true, y_pred, zero_division=0),
    }
    if y_prob is not None:
        metrics["ROC_AUC"] = roc_auc_score(y_true, y_prob)
        metrics["PR_AUC"] = average_precision_score(y_true, y_prob)
    else:
        metrics["ROC_AUC"] = np.nan
        metrics["PR_AUC"] = np.nan
    return metrics


def train_baseline_and_imbalance_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    preprocessor: ColumnTransformer,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Trains 6 machine learning algorithms across Baseline, Balanced Class Weights,

    and SMOTE imbalance mitigation strategies.
    """
    print("\n[2/8] Training 6 Machine Learning Algorithms across 3 Imbalance Settings...")
    fe = TelecomFeatureEngineer()

    # Calculate scale_pos_weight for XGBoost: negative_count / positive_count
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    xgb_scale_pos_weight = neg_count / pos_count

    algorithms = {
        "Logistic Regression": {
            "baseline": LogisticRegression(max_iter=1000, random_state=42),
            "balanced": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        },
        "Decision Tree": {
            "baseline": DecisionTreeClassifier(random_state=42),
            "balanced": DecisionTreeClassifier(class_weight="balanced", random_state=42),
        },
        "Random Forest": {
            "baseline": RandomForestClassifier(n_estimators=100, random_state=42),
            "balanced": RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42),
        },
        "XGBoost": {
            "baseline": XGBClassifier(eval_metric="logloss", random_state=42),
            "balanced": XGBClassifier(eval_metric="logloss", scale_pos_weight=xgb_scale_pos_weight, random_state=42),
        },
        "Gradient Boosting": {
            "baseline": GradientBoostingClassifier(random_state=42),
            "balanced": GradientBoostingClassifier(random_state=42),  # GB baseline used for SMOTE comparison
        },
        "Support Vector Machine": {
            "baseline": SVC(probability=True, random_state=42),
            "balanced": SVC(probability=True, class_weight="balanced", random_state=42),
        },
    }

    results = []
    trained_pipelines = {}

    for name, variants in algorithms.items():
        # 1. Baseline
        t0 = time.time()
        pipe_base = ImbPipeline([("fe", fe), ("preprocessor", preprocessor), ("classifier", variants["baseline"])])
        pipe_base.fit(X_train, y_train)
        fit_time = time.time() - t0

        y_pred = pipe_base.predict(X_test)
        y_prob = pipe_base.predict_proba(X_test)[:, 1] if hasattr(pipe_base.named_steps["classifier"], "predict_proba") else None
        m_base = evaluate_predictions(y_test, y_pred, y_prob)
        m_base.update({"Model": name, "Strategy": "Baseline", "Fit_Time_Sec": round(fit_time, 2)})
        results.append(m_base)
        trained_pipelines[f"{name}_Baseline"] = pipe_base
        print(f"      {name:22s} [Baseline] - Acc: {m_base['Accuracy']:.3f} | F1: {m_base['F1_Score']:.3f} | Recall: {m_base['Recall']:.3f} | ROC-AUC: {m_base['ROC_AUC']:.3f}")

        # 2. Balanced Class Weight
        t0 = time.time()
        pipe_bal = ImbPipeline([("fe", fe), ("preprocessor", preprocessor), ("classifier", variants["balanced"])])
        pipe_bal.fit(X_train, y_train)
        fit_time = time.time() - t0

        y_pred = pipe_bal.predict(X_test)
        y_prob = pipe_bal.predict_proba(X_test)[:, 1] if hasattr(pipe_bal.named_steps["classifier"], "predict_proba") else None
        m_bal = evaluate_predictions(y_test, y_pred, y_prob)
        m_bal.update({"Model": name, "Strategy": "Class_Weight_Balanced", "Fit_Time_Sec": round(fit_time, 2)})
        results.append(m_bal)
        trained_pipelines[f"{name}_Balanced"] = pipe_bal
        print(f"      {name:22s} [Balanced] - Acc: {m_bal['Accuracy']:.3f} | F1: {m_bal['F1_Score']:.3f} | Recall: {m_bal['Recall']:.3f} | ROC-AUC: {m_bal['ROC_AUC']:.3f}")

        # 3. SMOTE
        t0 = time.time()
        pipe_smote = ImbPipeline([
            ("fe", fe),
            ("preprocessor", preprocessor),
            ("smote", SMOTE(random_state=42)),
            ("classifier", variants["baseline"]),
        ])
        pipe_smote.fit(X_train, y_train)
        fit_time = time.time() - t0

        y_pred = pipe_smote.predict(X_test)
        y_prob = pipe_smote.predict_proba(X_test)[:, 1] if hasattr(pipe_smote.named_steps["classifier"], "predict_proba") else None
        m_smote = evaluate_predictions(y_test, y_pred, y_prob)
        m_smote.update({"Model": name, "Strategy": "SMOTE", "Fit_Time_Sec": round(fit_time, 2)})
        results.append(m_smote)
        trained_pipelines[f"{name}_SMOTE"] = pipe_smote
        print(f"      {name:22s} [SMOTE]    - Acc: {m_smote['Accuracy']:.3f} | F1: {m_smote['F1_Score']:.3f} | Recall: {m_smote['Recall']:.3f} | ROC-AUC: {m_smote['ROC_AUC']:.3f}")

    df_results = pd.DataFrame(results)
    return df_results, trained_pipelines


def tune_candidate_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    preprocessor: ColumnTransformer,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Performs Stratified 5-Fold Cross Validation Hyperparameter Optimization

    on the 5 required models: Random Forest, XGBoost, Gradient Boosting, Logistic Regression, and SVM.
    """
    print("\n[3/8] Running Stratified 5-Fold CV Hyperparameter Tuning on 5 Models...")
    fe = TelecomFeatureEngineer()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    tuning_configs = {
        "Random Forest": {
            "pipeline": ImbPipeline([
                ("fe", fe),
                ("preprocessor", preprocessor),
                ("classifier", RandomForestClassifier(random_state=42)),
            ]),
            "param_dist": {
                "classifier__n_estimators": [100, 150, 200],
                "classifier__max_depth": [6, 8, 10, None],
                "classifier__min_samples_split": [2, 5, 10],
                "classifier__min_samples_leaf": [1, 2, 4],
                "classifier__class_weight": ["balanced", "balanced_subsample"],
            },
            "n_iter": 8,
        },
        "XGBoost": {
            "pipeline": ImbPipeline([
                ("fe", fe),
                ("preprocessor", preprocessor),
                ("classifier", XGBClassifier(eval_metric="logloss", random_state=42)),
            ]),
            "param_dist": {
                "classifier__n_estimators": [100, 150, 200],
                "classifier__max_depth": [3, 4, 5],
                "classifier__learning_rate": [0.03, 0.05, 0.1],
                "classifier__subsample": [0.8, 1.0],
                "classifier__colsample_bytree": [0.8, 1.0],
                "classifier__scale_pos_weight": [1.5, 2.0, 2.77],
            },
            "n_iter": 8,
        },
        "Gradient Boosting": {
            "pipeline": ImbPipeline([
                ("fe", fe),
                ("preprocessor", preprocessor),
                ("smote", SMOTE(random_state=42)),
                ("classifier", GradientBoostingClassifier(random_state=42)),
            ]),
            "param_dist": {
                "classifier__n_estimators": [100, 150],
                "classifier__learning_rate": [0.03, 0.05, 0.1],
                "classifier__max_depth": [3, 4],
                "classifier__subsample": [0.8, 1.0],
            },
            "n_iter": 6,
        },
        "Logistic Regression": {
            "pipeline": ImbPipeline([
                ("fe", fe),
                ("preprocessor", preprocessor),
                ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
            ]),
            "param_dist": {
                "classifier__C": [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
                "classifier__penalty": ["l2"],
                "classifier__class_weight": ["balanced", None],
            },
            "n_iter": 7,
        },
        "Support Vector Machine": {
            "pipeline": ImbPipeline([
                ("fe", fe),
                ("preprocessor", preprocessor),
                ("classifier", SVC(probability=True, random_state=42)),
            ]),
            "param_dist": {
                "classifier__C": [0.5, 1.0, 2.0],
                "classifier__kernel": ["rbf"],
                "classifier__class_weight": ["balanced", None],
            },
            "n_iter": 3,
        },
    }

    tuned_results = []
    tuned_models = {}

    for name, config in tuning_configs.items():
        t0 = time.time()
        search = RandomizedSearchCV(
            estimator=config["pipeline"],
            param_distributions=config["param_dist"],
            n_iter=config["n_iter"],
            scoring="f1",
            cv=cv,
            random_state=42,
            n_jobs=-1,
        )
        search.fit(X_train, y_train)
        tuning_time = time.time() - t0

        best_pipe = search.best_estimator_
        y_pred = best_pipe.predict(X_test)
        y_prob = best_pipe.predict_proba(X_test)[:, 1] if hasattr(best_pipe.named_steps["classifier"], "predict_proba") else None

        metrics = evaluate_predictions(y_test, y_pred, y_prob)
        metrics.update({
            "Model": f"{name} (Tuned)",
            "Strategy": "Hyperparameter_Tuned",
            "Fit_Time_Sec": round(tuning_time, 2),
            "CV_F1_Score": round(search.best_score_, 4),
            "Best_Params": str(search.best_params_),
        })
        tuned_results.append(metrics)
        tuned_models[name] = {
            "pipeline": best_pipe,
            "best_params": search.best_params_,
            "cv_score": search.best_score_,
        }
        print(f"      {name:22s} (Tuned) - Test F1: {metrics['F1_Score']:.3f} | Recall: {metrics['Recall']:.3f} | ROC-AUC: {metrics['ROC_AUC']:.3f} | PR-AUC: {metrics['PR_AUC']:.3f}")

    df_tuned = pd.DataFrame(tuned_results)
    return df_tuned, tuned_models


def select_best_model(all_results: pd.DataFrame, tuned_models: Dict[str, Any], all_pipelines: Dict[str, Any]):
    """Selects the best overall model based on a balanced scoring formula:

    Balance Score = 0.30 * F1 + 0.25 * PR_AUC + 0.20 * ROC_AUC + 0.15 * Recall + 0.10 * Accuracy
    This strictly avoids picking models solely based on raw accuracy.
    """
    print("\n[4/8] Selecting Best Model using Balanced Multi-Metric Criteria...")
    df_eval = all_results.copy()
    df_eval["Balance_Score"] = (
        0.30 * df_eval["F1_Score"]
        + 0.25 * df_eval["PR_AUC"]
        + 0.20 * df_eval["ROC_AUC"]
        + 0.15 * df_eval["Recall"]
        + 0.10 * df_eval["Accuracy"]
    )
    df_eval = df_eval.sort_values(by="Balance_Score", ascending=False).reset_index(drop=True)
    best_row = df_eval.iloc[0]

    model_name_full = best_row["Model"]
    strategy = best_row["Strategy"]
    print(f"      >>> Selected Best Model: {model_name_full} [{strategy}]")
    print(f"          - Accuracy:          {best_row['Accuracy']:.4f}")
    print(f"          - Balanced Accuracy: {best_row['Balanced_Accuracy']:.4f}")
    print(f"          - Precision:         {best_row['Precision']:.4f}")
    print(f"          - Recall:            {best_row['Recall']:.4f}")
    print(f"          - F1-Score:          {best_row['F1_Score']:.4f}")
    print(f"          - ROC-AUC:           {best_row['ROC_AUC']:.4f}")
    print(f"          - PR-AUC:            {best_row['PR_AUC']:.4f}")
    print(f"          - Composite Score:   {best_row['Balance_Score']:.4f}")

    # Retrieve the trained pipeline
    base_name = model_name_full.replace(" (Tuned)", "")
    if "(Tuned)" in model_name_full and base_name in tuned_models:
        best_pipeline = tuned_models[base_name]["pipeline"]
        best_params = tuned_models[base_name]["best_params"]
    else:
        key = f"{base_name}_{strategy}"
        best_pipeline = all_pipelines.get(key, list(all_pipelines.values())[0])
        best_params = best_pipeline.named_steps["classifier"].get_params()

    return best_pipeline, best_row, df_eval, best_params


def generate_evaluation_visualizations(
    best_pipeline: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    all_results: pd.DataFrame,
    best_row: pd.Series,
):
    """Generates and saves Confusion Matrix, ROC Curve, PR Curve,

    Model Accuracy Comparison, and Model F1-score Comparison.
    """
    print("\n[5/8] Generating Evaluation Curves and Comparison Charts...")
    y_pred = best_pipeline.predict(X_test)
    y_prob = best_pipeline.predict_proba(X_test)[:, 1]

    # 1. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Retained (0)", "Churned (1)"],
        yticklabels=["Retained (0)", "Churned (1)"],
        ax=ax,
        annot_kws={"size": 14, "weight": "bold"},
    )
    ax.set_title(f"Confusion Matrix - {best_row['Model']}", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Predicted Label", fontsize=11, labelpad=8)
    ax.set_ylabel("True Label", fontsize=11, labelpad=8)
    plt.tight_layout()
    cm_path = OUTPUTS_DIR / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=300)
    plt.close()
    print(f"      Saved: {cm_path.resolve()}")

    # 2. ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, color="#2b5c8f", lw=2.5, label=f"{best_row['Model']} (AUC = {best_row['ROC_AUC']:.3f})")
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", lw=1.5, label="Random Guess (AUC = 0.500)")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    ax.set_ylabel("True Positive Rate (Recall)", fontsize=11)
    ax.set_title("Receiver Operating Characteristic (ROC) Curve", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    roc_path = OUTPUTS_DIR / "roc_curve.png"
    fig.savefig(roc_path, dpi=300)
    plt.close()
    print(f"      Saved: {roc_path.resolve()}")

    # 3. Precision-Recall Curve
    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(recall, precision, color="#d95f02", lw=2.5, label=f"{best_row['Model']} (PR-AUC = {best_row['PR_AUC']:.3f})")
    baseline_churn_rate = y_test.mean()
    ax.axhline(baseline_churn_rate, color="gray", linestyle="--", lw=1.5, label=f"No Skill (Rate = {baseline_churn_rate:.3f})")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Recall", fontsize=11)
    ax.set_ylabel("Precision", fontsize=11)
    ax.set_title("Precision-Recall (PR) Curve", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="lower left", frameon=True)
    plt.tight_layout()
    pr_path = OUTPUTS_DIR / "precision_recall_curve.png"
    fig.savefig(pr_path, dpi=300)
    plt.close()
    print(f"      Saved: {pr_path.resolve()}")

    # 4. Model Accuracy Comparison Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    top_models = all_results.sort_values(by="Accuracy", ascending=True)
    y_labels = [f"{m} ({s[:8]})" for m, s in zip(top_models["Model"], top_models["Strategy"])]
    bars = ax.barh(y_labels, top_models["Accuracy"], color="#3182bd", edgecolor="black", alpha=0.85, height=0.6)
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.01, bar.get_y() + bar.get_height() / 2, f"{w:.3f}", va="center", ha="left", fontsize=9, fontweight="bold")
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Accuracy Score", fontsize=11)
    ax.set_title("Model Accuracy Comparison Across Algorithms & Strategies", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    acc_path = OUTPUTS_DIR / "model_accuracy_comparison.png"
    fig.savefig(acc_path, dpi=300)
    plt.close()
    print(f"      Saved: {acc_path.resolve()}")

    # 5. Model F1-Score Comparison Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    top_f1 = all_results.sort_values(by="F1_Score", ascending=True)
    y_labels_f1 = [f"{m} ({s[:8]})" for m, s in zip(top_f1["Model"], top_f1["Strategy"])]
    bars_f1 = ax.barh(y_labels_f1, top_f1["F1_Score"], color="#e6550d", edgecolor="black", alpha=0.85, height=0.6)
    for bar in bars_f1:
        w = bar.get_width()
        ax.text(w + 0.01, bar.get_y() + bar.get_height() / 2, f"{w:.3f}", va="center", ha="left", fontsize=9, fontweight="bold")
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("F1-Score (Minority Churn Class)", fontsize=11)
    ax.set_title("Model F1-Score Comparison Across Algorithms & Strategies", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    f1_path = OUTPUTS_DIR / "model_f1_comparison.png"
    fig.savefig(f1_path, dpi=300)
    plt.close()
    print(f"      Saved: {f1_path.resolve()}")


def analyze_feature_importance(
    best_pipeline: Any,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    preprocessor: ColumnTransformer,
) -> pd.DataFrame:
    """Computes Random Forest, XGBoost, and Permutation Feature Importances,

    generates the top 15 feature importance chart, and returns the importance table.
    """
    print("\n[6/8] Analyzing Feature Importance (Trees & Permutation)...")
    fe = TelecomFeatureEngineer()
    X_fe_train = fe.transform(X_train)
    preprocessor.fit(X_fe_train)
    raw_feature_names = preprocessor.get_feature_names_out()

    # Clean feature names for clean presentation
    clean_names = [name.replace("num__", "").replace("cat__", "") for name in raw_feature_names]

    # 1. Permutation Importance on the Test Set
    print("      Calculating Permutation Importance on Test Set...")
    perm_res = permutation_importance(
        best_pipeline, X_test, y_test, n_repeats=10, random_state=42, scoring="f1", n_jobs=-1
    )
    perm_importances = perm_res.importances_mean

    # 2. Extract Classifier Feature Importances
    clf = best_pipeline.named_steps["classifier"]
    tree_importances = None
    if hasattr(clf, "feature_importances_"):
        tree_importances = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        tree_importances = np.abs(clf.coef_[0])

    df_imp = pd.DataFrame({
        "Feature": clean_names,
        "Permutation_Importance": perm_importances if len(perm_importances) == len(clean_names) else np.zeros(len(clean_names)),
    })
    if tree_importances is not None and len(tree_importances) == len(clean_names):
        df_imp["Model_Internal_Importance"] = tree_importances
        sort_col = "Model_Internal_Importance"
    else:
        sort_col = "Permutation_Importance"

    df_imp = df_imp.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
    top15 = df_imp.head(15).sort_values(by=sort_col, ascending=True)

    # Plot Top 15 Feature Importances
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(top15["Feature"], top15[sort_col], color="#2ca02c", edgecolor="black", alpha=0.85, height=0.6)
    for bar in bars:
        w = bar.get_width()
        ax.text(w * 1.02, bar.get_y() + bar.get_height() / 2, f"{w:.4f}", va="center", ha="left", fontsize=9, fontweight="bold")

    ax.set_title(f"Top 15 Most Influential Features on Customer Churn ({sort_col.replace('_', ' ')})", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Relative Importance Score", fontsize=11)
    plt.tight_layout()
    imp_path = OUTPUTS_DIR / "feature_importance.png"
    fig.savefig(imp_path, dpi=300)
    plt.close()
    print(f"      Saved: {imp_path.resolve()}")

    return df_imp


def save_final_pipeline_and_metadata(
    best_pipeline: Any,
    best_row: pd.Series,
    best_params: Dict[str, Any],
    all_results: pd.DataFrame,
    df_imp: pd.DataFrame,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
):
    """Saves the complete deployable pipeline, metadata, and metric comparisons."""
    print("\n[7/8] Saving Model Pipeline and Comprehensive Metadata...")

    # 1. Save Complete Pipeline with Joblib
    model_path = MODELS_DIR / "best_churn_model.pkl"
    joblib.dump(best_pipeline, model_path)
    print(f"      Saved pipeline to: {model_path.resolve()} ({os.path.getsize(model_path) / 1024:.1f} KB)")

    # 2. Save Comparison CSV
    comparison_path = OUTPUTS_DIR / "model_comparison.csv"
    all_results.to_csv(comparison_path, index=False)
    print(f"      Saved comparison table to: {comparison_path.resolve()}")

    # 3. Save Model Metadata JSON
    metadata = {
        "model_name": str(best_row["Model"]),
        "strategy": str(best_row["Strategy"]),
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "train_churn_rate": float(y_train.mean()),
        "test_churn_rate": float(y_test.mean()),
        "best_hyperparameters": {k: str(v) for k, v in best_params.items()},
        "test_performance_metrics": {
            "Accuracy": float(best_row["Accuracy"]),
            "Balanced_Accuracy": float(best_row["Balanced_Accuracy"]),
            "Precision": float(best_row["Precision"]),
            "Recall": float(best_row["Recall"]),
            "F1_Score": float(best_row["F1_Score"]),
            "ROC_AUC": float(best_row["ROC_AUC"]) if pd.notna(best_row["ROC_AUC"]) else None,
            "PR_AUC": float(best_row["PR_AUC"]) if pd.notna(best_row["PR_AUC"]) else None,
            "Composite_Balance_Score": float(best_row["Balance_Score"]),
        },
        "top_10_features": df_imp.head(10)[["Feature"]].to_dict(orient="records"),
        "training_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    meta_path = MODELS_DIR / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"      Saved metadata to: {meta_path.resolve()}")


def verify_end_to_end_inference(best_pipeline: Any, X_test: pd.DataFrame):
    """Verifies that the saved pipeline can take raw customer records directly

    and return valid probability and class predictions.
    """
    print("\n[8/8] Verifying End-to-End Pipeline Inference...")
    sample_record = X_test.iloc[:3]
    pred_classes = best_pipeline.predict(sample_record)
    pred_probs = best_pipeline.predict_proba(sample_record)[:, 1]

    for i in range(len(sample_record)):
        cid = sample_record.iloc[i].get("customerID", f"Customer-{i+1}")
        print(f"      Record {i+1} [{cid}]: Churn Prediction = {pred_classes[i]} | Churn Probability = {pred_probs[i]:.4f}")
    print("      Verification successful: Pipeline accepts raw input and produces valid inference.")


def main():
    print("=" * 75)
    print(" TELECOM CUSTOMER CHURN PREDICTION - COMPLETE TRAINING PIPELINE")
    print("=" * 75)
    t_start = time.time()

    # Step 1: Load and split
    X_train, X_test, y_train, y_test = load_and_split_data()

    # Step 2: Build Preprocessor
    preprocessor, num_cols, cat_cols = build_preprocessor(X_train)

    # Step 3: Train 6 algorithms x 3 imbalance strategies
    df_baseline, trained_pipes = train_baseline_and_imbalance_models(
        X_train, y_train, X_test, y_test, preprocessor
    )

    # Step 4: Hyperparameter Optimization on 5 candidate models
    df_tuned, tuned_models = tune_candidate_models(
        X_train, y_train, X_test, y_test, preprocessor
    )

    # Step 5: Combine results and select best model
    all_results = pd.concat([df_baseline, df_tuned], ignore_index=True)
    best_pipeline, best_row, df_eval, best_params = select_best_model(
        all_results, tuned_models, trained_pipes
    )

    # Step 6: Generate all evaluation curves & charts
    generate_evaluation_visualizations(
        best_pipeline, X_test, y_test, df_eval, best_row
    )

    # Step 7: Feature importance analysis
    df_imp = analyze_feature_importance(
        best_pipeline, X_train, y_train, X_test, y_test, preprocessor
    )

    # Step 8: Save pipeline, metadata, and verify inference
    save_final_pipeline_and_metadata(
        best_pipeline, best_row, best_params, df_eval, df_imp, X_train, X_test, y_train, y_test
    )
    verify_end_to_end_inference(best_pipeline, X_test)

    total_time = time.time() - t_start
    print("\n" + "=" * 75)
    print(f" TRAINING PIPELINE COMPLETED SUCCESSFULLY IN {total_time:.2f} SECONDS")
    print("=" * 75)


if __name__ == "__main__":
    main()
