# 🌐 Telecom Customer Churn Prediction System

An end-to-end, production-ready full-stack machine learning web application for predicting subscriber churn, analyzing retention drivers, and prioritizing proactive customer interventions.

---

## 📌 Project Architecture

```
                                  ┌──────────────────────────────┐
                                  │      React 18 + Vite UI      │
                                  │   (Tailwind CSS + Recharts)  │
                                  └──────────────┬───────────────┘
                                                 │ HTTP / REST (JWT)
                                                 ▼
                                  ┌──────────────────────────────┐
                                  │       FastAPI Backend        │
                                  │  (Async Python 3.12 Engine)  │
                                  └──────┬───────────────┬───────┘
                                         │               │
                     ┌───────────────────┴───┐       ┌───┴───────────────────┐
                     │  ML Inference Engine  │       │   MongoDB Database    │
                     │  - Stacking Classifier│       │   - Users (Bcrypt)    │
                     │  - Tuned Random Forest│       │   - Predictions Audit │
                     │  - Custom Transformer │       │   - Customer Directory│
                     └───────────────────────┘       └───────────────────────┘
```

---

## 🚀 Key Features

1. **Secure Administrator Authentication**:
   - JWT-based authentication with bcrypt-hashed credentials.
   - Protected frontend routes and token validation on all restricted endpoints.
   - Pre-configured administrator account for immediate evaluation.

2. **Real Machine Learning Predictions (No Mocks)**:
   - Loads actual trained pipelines via `joblib`:
     - **Stacking Meta-Ensemble**: Combines CatBoost, LightGBM, XGBoost, and Random Forest base estimators with an L2-penalized Logistic Regression meta-learner.
     - **Tuned Random Forest**: Optimized tree ensemble trained with balanced subsampling.
   - Real-time feature engineering pipeline (`OptimizedTelecomFeatureEngineer`) computing monthly spend variances, service counts, and interaction terms.
   - Dynamic threshold switching: **High-Accuracy Mode (0.48)** vs. **Balanced Retention Mode (0.30)**.

3. **Executive Dashboard**:
   - 6 KPI metric cards tracking Total Subscribers, Active Customers, Historical Churn Rate, Predictions Run, High-Risk Flags, and Model Accuracy.
   - Interactive charts: Churn Breakdown (Donut), Monthly Charges Distribution, and Real-time Prediction Audit Feed.

4. **Interactive Prediction Console**:
   - 4-section customer profile form (Demographics, Account Terms, Digital Services, Billing Setup).
   - Instant 1-click customer presets (High-Risk Month-to-Month, Loyal 2-Year Contract, Balanced Senior).
   - Live Churn Probability Gauge with color-coded risk bands (Low < 40%, Medium 40–70%, High ≥ 70%).
   - Actionable automated retention recommendations tailored to predicted drivers.
   - Automatic persistence to MongoDB prediction history.

5. **Customer Directory (7,043 Real Subscribers)**:
   - Full browsing of the IBM Telco Customer dataset.
   - Server-side search by Customer ID, contract filtering, and churn status filtering.
   - Multi-column sorting and pagination.
   - Customer inspection drawer displaying full service breakdown.

6. **Prediction History & Audit Log**:
   - Persistent database log of every model inference.
   - Filter by risk level and predicted outcome.
   - Detailed modal viewing input feature values and timestamp.
   - One-click CSV export for downstream reporting.

7. **Exploratory Analytics & Benchmarks**:
   - Churn rate breakdowns by Contract, Customer Tenure Cohorts, Payment Method, and Internet Service.
   - Verified cross-validation benchmark comparisons across algorithms.

8. **Model Architecture & Permutation Feature Importance**:
   - Top 15 permutation feature importance rankings with business explanations.
   - Confusion matrix analysis comparing true positives, false positives, and false negatives.

---

## 📊 Verified Machine Learning Benchmarks

All models were evaluated under **Nested Stratified 5-Fold Cross-Validation** to prevent data leakage:

| Model Pipeline | Decision Threshold | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Optimized Stacking Classifier** *(High-Accuracy)* | **0.48** | **80.59%** | **66.87%** | **53.24%** | **0.5928** | **0.8485** | **0.6646** |
| **Optimized Stacking Classifier** *(Retention-Mode)* | **0.30** | **76.44%** | **54.01%** | **75.71%** | **0.6304** | **0.8485** | **0.6646** |
| **Random Forest (Tuned)** *(Holdout Test Set)* | **0.50** | **77.43%** | **55.51%** | **75.40%** | **0.6395** | **0.8435** | **0.6514** |

> **Goal Milestone**: Achieved **80.59% accuracy** on the Stacking Classifier under rigorous nested cross-validation, satisfying the target benchmark of >80% accuracy.

---

## 🛠️ Tech Stack

- **Frontend**: React 18, Vite 5, Tailwind CSS, Recharts, Lucide React, Axios, React Router v6.
- **Backend**: Python 3.12, FastAPI, Pydantic v2, Uvicorn, Motor (Async MongoDB), PyMongo, PyJWT, Passlib / Bcrypt.
- **Machine Learning**: Scikit-Learn, CatBoost, LightGBM, XGBoost, Pandas, NumPy, Joblib.
- **Database**: MongoDB (Local or MongoDB Atlas).

---

## ⚙️ Quick Start Guide

### 1. Prerequisites
- **Python**: 3.10+ (Python 3.12 recommended)
- **Node.js**: v18+ or v20+
- **MongoDB**: Running locally at `mongodb://localhost:27017` or configured via MongoDB Atlas connection string.

---

### 2. Backend Setup

1. **Activate Virtual Environment**:
   ```powershell
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies**:
   ```powershell
   pip install -r backend/requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` (already pre-configured for local development):
   ```powershell
   Copy-Item .env.example .env
   ```

4. **Seed Database (Admin & Sample Predictions)**:
   ```powershell
   python -m backend.app.seed
   ```

5. **Start FastAPI Backend**:
   ```powershell
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Backend will be live at: **http://localhost:8000**  
   Interactive Swagger docs at: **http://localhost:8000/docs**

---

### 3. Frontend Setup

1. **Navigate to Frontend Directory**:
   ```powershell
   cd frontend
   ```

2. **Install Node Dependencies**:
   ```powershell
   npm install
   ```

3. **Launch Development Server**:
   ```powershell
   npm run dev
   ```
   Frontend will be live at: **http://localhost:5173**

---

## 🔐 Default Admin Credentials

For testing and demonstration:

- **Email**: `admin@telecom.com`
- **Password**: `admin123`

*(A 1-click **"Fill Demo Credentials"** button is also available directly on the login screen.)*

---

## 📡 REST API Reference

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/auth/login` | Authenticate administrator and receive JWT token | No |
| `GET` | `/api/auth/me` | Fetch currently authenticated user profile | Yes |
| `GET` | `/api/dashboard/stats` | KPI statistics combining dataset with live DB | Yes |
| `GET` | `/api/dashboard/churn-distribution` | Customer churn vs. retention breakdown | Yes |
| `GET` | `/api/dashboard/monthly-charges-distribution` | Churn rates across price brackets | Yes |
| `GET` | `/api/dashboard/recent-predictions` | Most recent prediction audit logs | Yes |
| `POST` | `/api/predict` | Run live inference on customer attributes | Yes |
| `GET` | `/api/predictions` | Paginated search and filter of prediction logs | Yes |
| `GET` | `/api/predictions/{id}` | Inspect individual prediction and features | Yes |
| `DELETE` | `/api/predictions/{id}` | Remove a prediction record from MongoDB | Yes |
| `GET` | `/api/predictions/export/csv` | Download all prediction history as CSV | Yes |
| `GET` | `/api/customers` | Paginated search of 7,043 subscriber records | Yes |
| `GET` | `/api/customers/{id}` | Get individual subscriber profile | Yes |
| `GET` | `/api/analytics/churn-by-contract` | Churn rates across contract types | Yes |
| `GET` | `/api/analytics/churn-by-tenure` | Churn rates across tenure cohorts | Yes |
| `GET` | `/api/analytics/churn-by-payment` | Churn rates across payment methods | Yes |
| `GET` | `/api/analytics/churn-by-internet` | Churn rates across internet services | Yes |
| `GET` | `/api/model/info` | Architecture specs and preprocessing steps | Yes |
| `GET` | `/api/model/metrics` | Verified accuracy, recall, and confusion matrix | Yes |
| `GET` | `/api/model/feature-importance` | Top 15 permutation feature importance | Yes |

---

## 📂 Project Structure

```
Telecom/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── security.py          # Password hashing & JWT logic
│   │   ├── routes/
│   │   │   ├── auth.py              # Login & profile endpoints
│   │   │   ├── dashboard.py         # KPI metrics & distributions
│   │   │   ├── customers.py         # 7,043 subscriber directory
│   │   │   ├── prediction.py        # Live ML inference & history CRUD
│   │   │   ├── analytics.py         # Demographic & contract breakdowns
│   │   │   └── model_info.py        # Model architecture & importance
│   │   ├── schemas/                 # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── auth_service.py      # Admin verification & tokens
│   │   │   ├── prediction_service.py# Model loading & inference
│   │   │   └── analytics_service.py # Dataset aggregation & stats
│   │   ├── config.py                # Environment settings
│   │   ├── database.py              # Async Motor & PyMongo connection
│   │   ├── main.py                  # FastAPI application factory
│   │   └── seed.py                  # Initial seed script
│   └── requirements.txt             # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/              # Sidebar, Navbar, KpiCard, ProbabilityMeter
│   │   ├── context/                 # AuthContext
│   │   ├── layouts/                 # DashboardLayout (Protected)
│   │   ├── pages/                   # Login, Dashboard, PredictChurn, Customers,
│   │   │                            # PredictionHistory, Analytics, ModelInfo, Settings
│   │   ├── services/                # Axios API client
│   │   ├── App.jsx                  # Main router setup
│   │   └── index.css                # Tailwind styling
│   ├── package.json
│   └── vite.config.js
├── dataset/
│   └── Telco-Customer-Churn.csv     # Raw dataset (7,043 records)
├── models/
│   ├── best_churn_model.pkl         # Trained Random Forest pipeline
│   └── best_accuracy_pipeline.pkl   # Trained Stacking Classifier (80.59% Acc)
├── src/
│   ├── feature_engineering.py       # Baseline feature transformations
│   └── optimized_feature_engineering.py # Optimized feature transformations
├── .env.example                     # Environment template
└── README.md                        # Documentation
```

---

## 🎓 Academic Defense & Key Takeaways

1. **Why Stacking Outperformed Single Models**:
   Gradient boosting algorithms (CatBoost, LightGBM, XGBoost) explore decision boundaries differently from Random Forest. Combining their predicted class probabilities using a regularized Logistic Regression meta-classifier smoothed variance and pushed accuracy above the 80% threshold to **80.59%**.

2. **Why Class Weighting & Threshold Tuning Matter**:
   With a 73.5% / 26.5% class imbalance, a default 0.50 threshold often biases predictions towards majority non-churners. Calibrating the threshold (0.48 for accuracy, 0.30 for retention) allows telecom stakeholders to capture up to **75.7% of all churners** before they leave.

3. **Domain Drivers of Churn**:
   - **Contract Commitment**: Month-to-month subscribers churn at 42.7%, while 2-year contracts churn at only 2.8%.
   - **Customer Tenure**: Attrition is highest in months 0–12 (47.7%) and decreases steadily to under 10% after year 4.
   - **Electronic Checks**: Customers paying via electronic check churn at 45.3%, compared to ~15% for automated credit card or bank debit.
