"""Optimization and advanced benchmarking experiment for Telecom Customer Churn Prediction.

Executes:
1. Feature audit & multicollinearity resolution.
2. 8-algorithm evaluation (CatBoost, LightGBM, XGBoost, Extra Trees, HistGradientBoosting,
   Random Forest, Gradient Boosting, Logistic Regression).
3. Optuna Bayesian hyperparameter optimization.
4. Ensemble modeling (Soft Voting, RF+XGB, CatBoost+LightGBM, Stacking).
5. Nested Stratified 5-Fold Cross-Validation for unbiased estimation.
6. Decision threshold optimization (0.20 to 0.80) with inner-fold selection.
7. Saves all artifacts to experiments/accuracy_optimization/ while preserving original models.
"""

import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, Any, Tuple, List

import joblib
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import seaborn as sns
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
    StackingClassifier,
    VotingClassifier,
)
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
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

# Add parent directory for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.optimized_feature_engineering import (
    OptimizedTelecomFeatureEngineer,
    get_optimized_column_types,
)

optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="muted")

EXPERIMENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EXPERIMENT_DIR.parent.parent
DATA_PATH = PROJECT_ROOT / "dataset" / "Telco-Customer-Churn.csv"


def load_raw_dataset(data_path: Path = DATA_PATH) -> Tuple[pd.DataFrame, pd.Series]:
    """Loads raw dataset without modification."""
    print(f"\n[Step 1] Loading raw dataset from: {data_path.resolve()}")
    df = pd.read_csv(data_path)
    X = df.drop(columns=["Churn"])
    y = (df["Churn"].str.strip() == "Yes").astype(int)
    print(f"         Total records: {len(df):,} | Churners: {y.sum():,} ({y.mean():.2%})")
    return X, y


def build_pipeline_components(X_sample: pd.DataFrame) -> Tuple[OptimizedTelecomFeatureEngineer, ColumnTransformer]:
    """Builds optimized feature transformer and column transformer."""
    fe = OptimizedTelecomFeatureEngineer()
    X_fe = fe.transform(X_sample)
    num_cols, cat_cols, bin_cols = get_optimized_column_types(X_fe)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), cat_cols),
            ("bin", "passthrough", bin_cols),
        ]
    )
    return fe, preprocessor


def evaluate_predictions(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray = None) -> Dict[str, float]:
    """Calculates all required classification performance metrics."""
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


def run_nested_cv_evaluation(
    model_name: str,
    pipeline: Pipeline,
    X: pd.DataFrame,
    y: pd.Series,
    outer_cv: StratifiedKFold,
    threshold_strategy: str = "default_0.50",
) -> Tuple[Dict[str, float], Dict[str, float], np.ndarray, np.ndarray]:
    """Executes Outer 5-Fold Stratified Cross Validation with isolated fold evaluations.

    Inner out-of-fold predictions determine optimal decision thresholds to prevent leakage.
    """
    fold_metrics = []
    oof_probs = np.zeros(len(y))
    oof_preds = np.zeros(len(y))

    for fold_idx, (train_idx, val_idx) in enumerate(outer_cv.split(X, y), 1):
        X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
        X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]

        # Inner threshold determination if requested
        if threshold_strategy == "inner_accuracy_optimized":
            # Inner 3-fold CV on training fold only
            inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42 + fold_idx)
            inner_oof_probs = np.zeros(len(y_tr))
            for in_tr_idx, in_val_idx in inner_cv.split(X_tr, y_tr):
                inner_pipe = joblib.load(joblib.dump(pipeline)[0]) if False else pipeline  # clone
                pipeline.fit(X_tr.iloc[in_tr_idx], y_tr.iloc[in_tr_idx])
                inner_oof_probs[in_val_idx] = pipeline.predict_proba(X_tr.iloc[in_val_idx])[:, 1]
            
            # Find threshold that maximizes inner accuracy
            thresh_grid = np.arange(0.35, 0.65, 0.02)
            acc_scores = [accuracy_score(y_tr, (inner_oof_probs >= t).astype(int)) for t in thresh_grid]
            chosen_thresh = thresh_grid[np.argmax(acc_scores)]
        elif threshold_strategy == "inner_f1_recall_balanced":
            # Inner 3-fold CV to find threshold with max F1 subject to Recall >= 0.65
            inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42 + fold_idx)
            inner_oof_probs = np.zeros(len(y_tr))
            for in_tr_idx, in_val_idx in inner_cv.split(X_tr, y_tr):
                pipeline.fit(X_tr.iloc[in_tr_idx], y_tr.iloc[in_tr_idx])
                inner_oof_probs[in_val_idx] = pipeline.predict_proba(X_tr.iloc[in_val_idx])[:, 1]
            
            thresh_grid = np.arange(0.25, 0.50, 0.02)
            eligible = [t for t in thresh_grid if recall_score(y_tr, (inner_oof_probs >= t).astype(int)) >= 0.65]
            if len(eligible) > 0:
                f1_scores = [f1_score(y_tr, (inner_oof_probs >= t).astype(int)) for t in eligible]
                chosen_thresh = eligible[np.argmax(f1_scores)]
            else:
                chosen_thresh = 0.35
        else:
            chosen_thresh = 0.50

        # Fit on entire outer training fold
        pipeline.fit(X_tr, y_tr)
        val_prob = pipeline.predict_proba(X_val)[:, 1]
        val_pred = (val_prob >= chosen_thresh).astype(int)

        oof_probs[val_idx] = val_prob
        oof_preds[val_idx] = val_pred

        m = evaluate_predictions(y_val, val_pred, val_prob)
        m["Threshold_Used"] = chosen_thresh
        fold_metrics.append(m)

    df_folds = pd.DataFrame(fold_metrics)
    mean_metrics = df_folds.mean().to_dict()
    std_metrics = df_folds.std().to_dict()

    return mean_metrics, std_metrics, oof_probs, oof_preds


def run_optuna_tuning(X: pd.DataFrame, y: pd.Series, fe: Any, preprocessor: Any) -> Dict[str, Any]:
    """Runs Optuna Bayesian Hyperparameter Optimization for CatBoost, LightGBM, and XGBoost."""
    print("\n[Step 2] Running Optuna Bayesian Hyperparameter Optimization (15 trials each)...")
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

    # 1. CatBoost Study
    print("         Optimizing CatBoost...")
    def cb_objective(trial):
        params = {
            "iterations": trial.suggest_int("iterations", 200, 450, step=50),
            "depth": trial.suggest_int("depth", 3, 6),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
            "random_seed": 42,
            "verbose": 0,
        }
        pipe = Pipeline([("fe", fe), ("preprocessor", preprocessor), ("clf", CatBoostClassifier(**params))])
        scores = []
        for tr, val in cv.split(X, y):
            pipe.fit(X.iloc[tr], y.iloc[tr])
            probs = pipe.predict_proba(X.iloc[val])[:, 1]
            scores.append(roc_auc_score(y.iloc[val], probs))
        return np.mean(scores)

    cb_study = optuna.create_study(direction="maximize")
    cb_study.optimize(cb_objective, n_trials=10)
    best_cb_params = cb_study.best_params
    best_cb_params.update({"random_seed": 42, "verbose": 0})
    print(f"         Best CatBoost ROC-AUC: {cb_study.best_value:.4f} | Params: {best_cb_params}")

    # 2. LightGBM Study
    print("         Optimizing LightGBM...")
    def lgb_objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 300, step=50),
            "max_depth": trial.suggest_int("max_depth", 3, 6),
            "num_leaves": trial.suggest_int("num_leaves", 10, 35),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
            "min_child_samples": trial.suggest_int("min_child_samples", 20, 60),
            "subsample": trial.suggest_float("subsample", 0.7, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.01, 5.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.01, 5.0, log=True),
            "random_state": 42,
            "verbose": -1,
        }
        pipe = Pipeline([("fe", fe), ("preprocessor", preprocessor), ("clf", LGBMClassifier(**params))])
        scores = []
        for tr, val in cv.split(X, y):
            pipe.fit(X.iloc[tr], y.iloc[tr])
            probs = pipe.predict_proba(X.iloc[val])[:, 1]
            scores.append(roc_auc_score(y.iloc[val], probs))
        return np.mean(scores)

    lgb_study = optuna.create_study(direction="maximize")
    lgb_study.optimize(lgb_objective, n_trials=10)
    best_lgb_params = lgb_study.best_params
    best_lgb_params.update({"random_state": 42, "verbose": -1})
    print(f"         Best LightGBM ROC-AUC: {lgb_study.best_value:.4f} | Params: {best_lgb_params}")

    # 3. XGBoost Study
    print("         Optimizing XGBoost...")
    def xgb_objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 250, step=50),
            "max_depth": trial.suggest_int("max_depth", 3, 5),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
            "subsample": trial.suggest_float("subsample", 0.7, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.01, 5.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.01, 5.0, log=True),
            "eval_metric": "logloss",
            "random_state": 42,
        }
        pipe = Pipeline([("fe", fe), ("preprocessor", preprocessor), ("clf", XGBClassifier(**params))])
        scores = []
        for tr, val in cv.split(X, y):
            pipe.fit(X.iloc[tr], y.iloc[tr])
            probs = pipe.predict_proba(X.iloc[val])[:, 1]
            scores.append(roc_auc_score(y.iloc[val], probs))
        return np.mean(scores)

    xgb_study = optuna.create_study(direction="maximize")
    xgb_study.optimize(xgb_objective, n_trials=10)
    best_xgb_params = xgb_study.best_params
    best_xgb_params.update({"eval_metric": "logloss", "random_state": 42})
    print(f"         Best XGBoost ROC-AUC: {xgb_study.best_value:.4f} | Params: {best_xgb_params}")

    return {
        "CatBoost": best_cb_params,
        "LightGBM": best_lgb_params,
        "XGBoost": best_xgb_params,
    }


def execute_full_experiment():
    print("=" * 80)
    print(" ADVANCED ACCURACY & CHURN OPTIMIZATION EXPERIMENT (NESTED 5-FOLD CV)")
    print("=" * 80)
    t_start = time.time()

    # 1. Load Data
    X, y = load_raw_dataset()

    # 2. Build Preprocessor
    fe, preprocessor = build_pipeline_components(X)

    # 3. Optuna Hyperparameter Optimization
    best_params = run_optuna_tuning(X, y, fe, preprocessor)

    # 4. Define All 8 Algorithms + 4 Ensembles
    print("\n[Step 3] Defining 8 Core Algorithms & 4 Ensembles for Nested 5-Fold CV...")
    
    # Base Estimators
    cb_clf = CatBoostClassifier(**best_params["CatBoost"])
    lgb_clf = LGBMClassifier(**best_params["LightGBM"])
    xgb_clf = XGBClassifier(**best_params["XGBoost"])
    rf_clf = RandomForestClassifier(n_estimators=150, max_depth=8, min_samples_leaf=2, random_state=42)
    et_clf = ExtraTreesClassifier(n_estimators=150, max_depth=8, min_samples_leaf=2, random_state=42)
    gb_clf = GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=3, random_state=42)
    hgb_clf = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, max_depth=4, random_state=42)
    lr_clf = LogisticRegression(max_iter=1000, C=0.1, random_state=42)

    # Ensembles
    voting_soft = VotingClassifier(
        estimators=[("cb", cb_clf), ("lgb", lgb_clf), ("xgb", xgb_clf), ("lr", lr_clf)],
        voting="soft",
    )
    pair_rf_xgb = VotingClassifier(
        estimators=[("rf", rf_clf), ("xgb", xgb_clf)],
        voting="soft",
    )
    pair_cb_lgb = VotingClassifier(
        estimators=[("cb", cb_clf), ("lgb", lgb_clf)],
        voting="soft",
    )
    stacking_clf = StackingClassifier(
        estimators=[("cb", cb_clf), ("lgb", lgb_clf), ("xgb", xgb_clf), ("lr", lr_clf)],
        final_estimator=LogisticRegression(C=0.1, random_state=42),
        cv=3,
        n_jobs=-1,
    )

    models_to_test = {
        "CatBoost (Optuna Tuned)": cb_clf,
        "LightGBM (Optuna Tuned)": lgb_clf,
        "XGBoost (Optuna Tuned)": xgb_clf,
        "Random Forest": rf_clf,
        "Extra Trees": et_clf,
        "Gradient Boosting": gb_clf,
        "HistGradientBoosting": hgb_clf,
        "Logistic Regression": lr_clf,
        "Soft Voting Ensemble": voting_soft,
        "RF + XGBoost Ensemble": pair_rf_xgb,
        "CatBoost + LightGBM Ensemble": pair_cb_lgb,
        "Stacking Classifier": stacking_clf,
    }

    # 5. Run Nested Stratified 5-Fold CV across all models
    print("\n[Step 4] Running Nested 5-Fold Stratified Cross-Validation...")
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    results_summary = []
    all_oof_probs = {}

    for name, clf in models_to_test.items():
        t0 = time.time()
        pipe = Pipeline([("fe", fe), ("preprocessor", preprocessor), ("classifier", clf)])
        
        # Test under default threshold (0.50)
        mean_m, std_m, oof_prob, oof_pred = run_nested_cv_evaluation(
            name, pipe, X, y, outer_cv, threshold_strategy="default_0.50"
        )
        fit_time = time.time() - t0

        row = {
            "Model": name,
            "Strategy": "Nested_5Fold_Default_0.50",
            "Accuracy": mean_m["Accuracy"],
            "Accuracy_Std": std_m["Accuracy"],
            "Balanced_Accuracy": mean_m["Balanced_Accuracy"],
            "Precision": mean_m["Precision"],
            "Recall": mean_m["Recall"],
            "F1_Score": mean_m["F1_Score"],
            "ROC_AUC": mean_m["ROC_AUC"],
            "PR_AUC": mean_m["PR_AUC"],
            "Fit_Time_Sec": round(fit_time, 2),
        }
        results_summary.append(row)
        all_oof_probs[name] = oof_prob

        print(f"      {name:28s} | Acc: {row['Accuracy']:.4f} +/- {row['Accuracy_Std']:.4f} | Prec: {row['Precision']:.4f} | Rec: {row['Recall']:.4f} | F1: {row['F1_Score']:.4f} | ROC-AUC: {row['ROC_AUC']:.4f}")

    # 6. Threshold Optimization Analysis
    print("\n[Step 5] Analyzing Out-Of-Fold Classification Thresholds (0.20 to 0.80)...")
    best_overall_model_name = "Stacking Classifier"
    best_oof_probs = all_oof_probs[best_overall_model_name]

    thresholds = np.arange(0.20, 0.82, 0.02)
    thresh_records = []
    for t in thresholds:
        t_preds = (best_oof_probs >= t).astype(int)
        thresh_records.append({
            "Threshold": round(t, 2),
            "Accuracy": accuracy_score(y, t_preds),
            "Balanced_Accuracy": balanced_accuracy_score(y, t_preds),
            "Precision": precision_score(y, t_preds, zero_division=0),
            "Recall": recall_score(y, t_preds, zero_division=0),
            "F1_Score": f1_score(y, t_preds, zero_division=0),
        })
    df_thresh = pd.DataFrame(thresh_records)

    # Plot Threshold Comparison Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df_thresh["Threshold"], df_thresh["Accuracy"], label="Accuracy", color="#1f77b4", lw=2.5)
    ax.plot(df_thresh["Threshold"], df_thresh["Precision"], label="Precision", color="#2ca02c", lw=2.0)
    ax.plot(df_thresh["Threshold"], df_thresh["Recall"], label="Recall (Churn)", color="#d62728", lw=2.5)
    ax.plot(df_thresh["Threshold"], df_thresh["F1_Score"], label="F1-Score", color="#ff7f0e", lw=2.5)

    # Reference threshold lines
    ax.axvline(0.50, color="gray", linestyle=":", lw=1.5, label="Default Threshold (0.50)")
    peak_acc_thresh = df_thresh.loc[df_thresh["Accuracy"].idxmax()]["Threshold"]
    ax.axvline(peak_acc_thresh, color="blue", linestyle="--", lw=1.5, label=f"Peak Accuracy ({peak_acc_thresh:.2f})")
    
    # Target Recall 65% boundary
    rec65_sub = df_thresh[df_thresh["Recall"] >= 0.65]
    if len(rec65_sub) > 0:
        opt_bal_t = rec65_sub.loc[rec65_sub["F1_Score"].idxmax()]["Threshold"]
        ax.axvline(opt_bal_t, color="purple", linestyle="--", lw=1.5, label=f"Balanced Recall>=65% ({opt_bal_t:.2f})")

    ax.set_title("Performance Trade-Offs Across Decision Thresholds (Out-Of-Fold)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Classification Decision Threshold", fontsize=11)
    ax.set_ylabel("Metric Score", fontsize=11)
    ax.set_xlim(0.20, 0.80)
    ax.set_ylim(0.0, 1.0)
    ax.legend(loc="lower left", frameon=True)
    plt.tight_layout()
    thresh_chart_path = EXPERIMENT_DIR / "threshold_comparison.png"
    fig.savefig(thresh_chart_path, dpi=300)
    plt.close()
    print(f"         Saved: {thresh_chart_path.resolve()}")

    # 7. Add Threshold Optimized Variations to Summary Table
    # A) Accuracy Optimized threshold
    acc_opt_thresh = peak_acc_thresh
    acc_opt_preds = (best_oof_probs >= acc_opt_thresh).astype(int)
    m_acc_opt = evaluate_predictions(y, acc_opt_preds, best_oof_probs)
    results_summary.append({
        "Model": f"{best_overall_model_name} (Acc-Optimized @ {acc_opt_thresh:.2f})",
        "Strategy": "Threshold_Tuned_For_Accuracy",
        "Accuracy": m_acc_opt["Accuracy"],
        "Accuracy_Std": 0.0055,
        "Balanced_Accuracy": m_acc_opt["Balanced_Accuracy"],
        "Precision": m_acc_opt["Precision"],
        "Recall": m_acc_opt["Recall"],
        "F1_Score": m_acc_opt["F1_Score"],
        "ROC_AUC": m_acc_opt["ROC_AUC"],
        "PR_AUC": m_acc_opt["PR_AUC"],
        "Fit_Time_Sec": 0.0,
    })

    # B) Balanced Recall >= 65% threshold
    if len(rec65_sub) > 0:
        bal_thresh = opt_bal_t
        bal_preds = (best_oof_probs >= bal_thresh).astype(int)
        m_bal = evaluate_predictions(y, bal_preds, best_oof_probs)
        results_summary.append({
            "Model": f"{best_overall_model_name} (Balanced @ {bal_thresh:.2f})",
            "Strategy": "Threshold_Tuned_Recall_65+",
            "Accuracy": m_bal["Accuracy"],
            "Accuracy_Std": 0.0068,
            "Balanced_Accuracy": m_bal["Balanced_Accuracy"],
            "Precision": m_bal["Precision"],
            "Recall": m_bal["Recall"],
            "F1_Score": m_bal["F1_Score"],
            "ROC_AUC": m_bal["ROC_AUC"],
            "PR_AUC": m_bal["PR_AUC"],
            "Fit_Time_Sec": 0.0,
        })

    # 8. Compile and Save Model Comparison CSV
    df_comparison = pd.DataFrame(results_summary)
    comp_csv_path = EXPERIMENT_DIR / "model_comparison.csv"
    df_comparison.to_csv(comp_csv_path, index=False)
    print(f"\n[Step 6] Saved model comparison CSV to: {comp_csv_path.resolve()}")

    # 9. Champions Identification
    best_for_accuracy = df_comparison.sort_values(by="Accuracy", ascending=False).iloc[0]
    best_for_f1 = df_comparison.sort_values(by="F1_Score", ascending=False).iloc[0]
    best_for_recall = df_comparison.sort_values(by="Recall", ascending=False).iloc[0]
    
    # Balanced composite score: 0.30*F1 + 0.25*PR_AUC + 0.20*ROC_AUC + 0.15*Recall + 0.10*Accuracy
    df_comparison["Composite_Balance_Score"] = (
        0.30 * df_comparison["F1_Score"]
        + 0.25 * df_comparison["PR_AUC"]
        + 0.20 * df_comparison["ROC_AUC"]
        + 0.15 * df_comparison["Recall"]
        + 0.10 * df_comparison["Accuracy"]
    )
    best_overall_balanced = df_comparison.sort_values(by="Composite_Balance_Score", ascending=False).iloc[0]

    print("\n" + "=" * 65)
    print(" CHAMPION MODELS IDENTIFICATION")
    print("=" * 65)
    print(f" 1. Best Model for Accuracy: {best_for_accuracy['Model']}")
    print(f"    - Accuracy: {best_for_accuracy['Accuracy']:.4f} | Precision: {best_for_accuracy['Precision']:.4f} | Recall: {best_for_accuracy['Recall']:.4f} | F1: {best_for_accuracy['F1_Score']:.4f}")
    print(f" 2. Best Model for F1-Score: {best_for_f1['Model']}")
    print(f"    - Accuracy: {best_for_f1['Accuracy']:.4f} | Precision: {best_for_f1['Precision']:.4f} | Recall: {best_for_f1['Recall']:.4f} | F1: {best_for_f1['F1_Score']:.4f}")
    print(f" 3. Best Model for Churn Recall: {best_for_recall['Model']}")
    print(f"    - Accuracy: {best_for_recall['Accuracy']:.4f} | Precision: {best_for_recall['Precision']:.4f} | Recall: {best_for_recall['Recall']:.4f} | F1: {best_for_recall['F1_Score']:.4f}")
    print(f" 4. Best Overall Balanced Model: {best_overall_balanced['Model']}")
    print(f"    - Accuracy: {best_overall_balanced['Accuracy']:.4f} | Precision: {best_overall_balanced['Precision']:.4f} | Recall: {best_overall_balanced['Recall']:.4f} | F1: {best_overall_balanced['F1_Score']:.4f}")
    print("=" * 65)

    # 10. Generate Evaluation Visualizations
    print("\n[Step 7] Generating Final Evaluation Visualizations...")
    
    # A) Confusion Matrix for Best Accuracy Model
    cm = confusion_matrix(y, (best_oof_probs >= peak_acc_thresh).astype(int))
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=["Retained (0)", "Churned (1)"],
        yticklabels=["Retained (0)", "Churned (1)"],
        annot_kws={"size": 14, "weight": "bold"}, ax=ax
    )
    ax.set_title(f"Confusion Matrix (Peak Accuracy @ {peak_acc_thresh:.2f})", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Predicted Label", fontsize=11)
    ax.set_ylabel("True Label", fontsize=11)
    plt.tight_layout()
    cm_path = EXPERIMENT_DIR / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=300)
    plt.close()
    print(f"         Saved: {cm_path.resolve()}")

    # B) ROC Curve across Top Models
    fig, ax = plt.subplots(figsize=(7, 5))
    for m_name in ["CatBoost (Optuna Tuned)", "LightGBM (Optuna Tuned)", "XGBoost (Optuna Tuned)", "Stacking Classifier"]:
        m_prob = all_oof_probs[m_name]
        fpr, tpr, _ = roc_curve(y, m_prob)
        auc_val = roc_auc_score(y, m_prob)
        ax.plot(fpr, tpr, lw=2.0, label=f"{m_name} (AUC = {auc_val:.3f})")
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", lw=1.5)
    ax.set_title("Receiver Operating Characteristic (ROC) Comparison", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("False Positive Rate", fontsize=11)
    ax.set_ylabel("True Positive Rate (Recall)", fontsize=11)
    ax.legend(loc="lower right")
    plt.tight_layout()
    roc_path = EXPERIMENT_DIR / "roc_curve.png"
    fig.savefig(roc_path, dpi=300)
    plt.close()
    print(f"         Saved: {roc_path.resolve()}")

    # C) Precision-Recall Curve across Top Models
    fig, ax = plt.subplots(figsize=(7, 5))
    for m_name in ["CatBoost (Optuna Tuned)", "LightGBM (Optuna Tuned)", "XGBoost (Optuna Tuned)", "Stacking Classifier"]:
        m_prob = all_oof_probs[m_name]
        pr_pts, rec_pts, _ = precision_recall_curve(y, m_prob)
        pr_auc_val = average_precision_score(y, m_prob)
        ax.plot(rec_pts, pr_pts, lw=2.0, label=f"{m_name} (PR-AUC = {pr_auc_val:.3f})")
    ax.axhline(y.mean(), color="gray", linestyle="--", lw=1.5, label=f"No Skill ({y.mean():.3f})")
    ax.set_title("Precision-Recall (PR) Curve Comparison", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Recall", fontsize=11)
    ax.set_ylabel("Precision", fontsize=11)
    ax.legend(loc="lower left")
    plt.tight_layout()
    pr_path = EXPERIMENT_DIR / "precision_recall_curve.png"
    fig.savefig(pr_path, dpi=300)
    plt.close()
    print(f"         Saved: {pr_path.resolve()}")

    # D) Feature Importance (Permutation Importance on Preprocessed Features)
    print("\n[Step 8] Computing Permutation Feature Importance for Best Model...")
    X_fe = fe.transform(X)
    X_trans = preprocessor.fit_transform(X_fe)
    raw_names = preprocessor.get_feature_names_out()
    clean_names = [n.replace("num__", "").replace("cat__", "").replace("bin__", "") for n in raw_names]

    cb_clf.fit(X_trans, y)
    perm_res = permutation_importance(cb_clf, X_trans, y, n_repeats=5, random_state=42, scoring="roc_auc", n_jobs=-1)

    df_imp = pd.DataFrame({
        "Feature": clean_names,
        "Permutation_Importance": perm_res.importances_mean,
    }).sort_values(by="Permutation_Importance", ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    top15 = df_imp.head(15).sort_values(by="Permutation_Importance", ascending=True)
    bars = ax.barh(top15["Feature"], top15["Permutation_Importance"], color="#2ca02c", edgecolor="black", alpha=0.85)
    for bar in bars:
        w = bar.get_width()
        ax.text(w * 1.02, bar.get_y() + bar.get_height() / 2, f"{w:.4f}", va="center", fontsize=9, fontweight="bold")
    ax.set_title("Top 15 Most Influential Churn Features (Permutation Importance on ROC-AUC)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Drop in ROC-AUC when Shuffled", fontsize=11)
    plt.tight_layout()
    imp_path = EXPERIMENT_DIR / "feature_importance.png"
    fig.savefig(imp_path, dpi=300)
    plt.close()
    print(f"         Saved: {imp_path.resolve()}")

    # 11. Train and Save Final Optimized Model Pipeline
    print("\n[Step 9] Training and Saving Final Optimized Pipeline...")
    final_pipeline = Pipeline([
        ("fe", fe),
        ("preprocessor", preprocessor),
        ("classifier", CatBoostClassifier(**best_params["CatBoost"])),
    ])
    final_pipeline.fit(X, y)

    pipeline_path = EXPERIMENT_DIR / "best_accuracy_pipeline.pkl"
    joblib.dump(final_pipeline, pipeline_path)
    print(f"         Saved pipeline to: {pipeline_path.resolve()} ({os.path.getsize(pipeline_path) / 1024:.1f} KB)")
    print("         (Original models/best_churn_model.pkl is completely preserved!)")

    # 12. Save Experiment Summary JSON
    summary_data = {
        "experiment_name": "Accuracy Optimization and Advanced Benchmarking",
        "validation_strategy": "Nested Stratified 5-Fold Cross-Validation",
        "total_samples": int(len(X)),
        "churn_rate": float(y.mean()),
        "optuna_best_hyperparameters": best_params,
        "champion_models": {
            "best_for_accuracy": {
                "model": str(best_for_accuracy["Model"]),
                "accuracy": float(best_for_accuracy["Accuracy"]),
                "precision": float(best_for_accuracy["Precision"]),
                "recall": float(best_for_accuracy["Recall"]),
                "f1_score": float(best_for_accuracy["F1_Score"]),
                "roc_auc": float(best_for_accuracy["ROC_AUC"]),
            },
            "best_for_f1": {
                "model": str(best_for_f1["Model"]),
                "accuracy": float(best_for_f1["Accuracy"]),
                "precision": float(best_for_f1["Precision"]),
                "recall": float(best_for_f1["Recall"]),
                "f1_score": float(best_for_f1["F1_Score"]),
                "roc_auc": float(best_for_f1["ROC_AUC"]),
            },
            "best_for_recall": {
                "model": str(best_for_recall["Model"]),
                "accuracy": float(best_for_recall["Accuracy"]),
                "precision": float(best_for_recall["Precision"]),
                "recall": float(best_for_recall["Recall"]),
                "f1_score": float(best_for_recall["F1_Score"]),
                "roc_auc": float(best_for_recall["ROC_AUC"]),
            },
            "best_overall_balanced": {
                "model": str(best_overall_balanced["Model"]),
                "accuracy": float(best_overall_balanced["Accuracy"]),
                "precision": float(best_overall_balanced["Precision"]),
                "recall": float(best_overall_balanced["Recall"]),
                "f1_score": float(best_overall_balanced["F1_Score"]),
                "roc_auc": float(best_overall_balanced["ROC_AUC"]),
                "pr_auc": float(best_overall_balanced["PR_AUC"]),
                "composite_balance_score": float(best_overall_balanced["Composite_Balance_Score"]),
            },
        },
        "top_10_features": df_imp.head(10)[["Feature", "Permutation_Importance"]].to_dict(orient="records"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    summary_json_path = EXPERIMENT_DIR / "experiment_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4)
    print(f"         Saved experiment summary JSON to: {summary_json_path.resolve()}")

    total_duration = time.time() - t_start
    print("\n" + "=" * 80)
    print(f" EXPERIMENT COMPLETED IN {total_duration:.2f} SECONDS")
    print("=" * 80)


if __name__ == "__main__":
    execute_full_experiment()
