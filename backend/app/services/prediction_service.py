"""Service layer for machine learning inference and prediction history."""

import csv
import io
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from bson import ObjectId

from backend.app.config import settings, BASE_DIR
from backend.app.database import get_database
from backend.app.schemas.prediction import (
    CustomerFeatures,
    PredictionResponse,
    PredictionHistoryItem,
    PredictionHistoryPagination,
)

# Add root directory to sys.path to allow unpickling custom transformers
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import feature engineer classes into module namespace so Joblib can deserialize them
from src.feature_engineering import TelecomFeatureEngineer
from src.optimized_feature_engineering import OptimizedTelecomFeatureEngineer

logger = logging.getLogger("telecom.prediction")


class PredictionService:
    """Manages model loading, inference execution, and database persistence using one fixed CatBoost pipeline."""

    MODEL_NAME = "CatBoost Classifier"
    FIXED_THRESHOLD = 0.50

    def __init__(self):
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        """Loads the verified CatBoost pipeline from experiments/accuracy_optimization/best_accuracy_pipeline.pkl."""
        model_path = settings.CATBOOST_MODEL_PATH
        if not model_path.exists() and settings.ALT_MODEL_PATH.exists():
            model_path = settings.ALT_MODEL_PATH

        try:
            if model_path.exists():
                self.pipeline = joblib.load(model_path)
                logger.info("Loaded CatBoost pipeline successfully from: %s", model_path)
            else:
                logger.error("CatBoost pipeline not found at: %s", model_path)
        except Exception as e:
            logger.error("Error loading CatBoost pipeline: %s", e)

    def get_model(self, _model_name: Optional[str] = None):
        """Returns the single active CatBoost pipeline."""
        if self.pipeline is not None:
            return self.pipeline, self.MODEL_NAME
        raise RuntimeError("CatBoost machine learning pipeline is not loaded in memory.")

    def calculate_risk_level(self, probability: float) -> str:
        """Assigns business-facing risk category based on churn probability."""
        if probability >= 0.70:
            return "High Risk"
        elif probability >= 0.40:
            return "Medium Risk"
        return "Low Risk"

    def generate_recommendation(self, risk_level: str, probability: float, features: Dict[str, Any]) -> str:
        """Generates pragmatic business retention advice based on customer risk and attributes."""
        contract = features.get("Contract", "Month-to-month")
        tenure = features.get("tenure", 0)
        payment = features.get("PaymentMethod", "")
        tech_support = features.get("TechSupport", "No")

        if risk_level == "High Risk":
            rec = "IMMEDIATE ACTION REQUIRED: Contact customer via proactive outreach. "
            if contract == "Month-to-month":
                rec += "Offer an incentive (e.g. 15% discount) to upgrade to an annual contract. "
            if tech_support == "No":
                rec += "Bundle complimentary technical support or cybersecurity protection. "
            if "check" in payment.lower():
                rec += "Encourage automated billing with a one-time statement credit."
            return rec
        elif risk_level == "Medium Risk":
            rec = "MONITOR & NURTURE: Customer displays moderate defection indicators. "
            if tenure <= 12:
                rec += "Schedule onboarding check-in call to ensure satisfaction with fiber/broadband speeds. "
            else:
                rec += "Send personalized loyalty rewards or service enhancement notifications."
            return rec
        else:
            return "HEALTHY RETENTION: Customer exhibits low churn risk. Maintain regular service quality and consider upsell to premium entertainment add-ons."

    async def predict_churn(
        self,
        features: CustomerFeatures,
        customer_id: Optional[str] = None,
        model_name: Optional[str] = None,
        threshold: Optional[float] = None,
        save_to_db: bool = False,
    ) -> PredictionResponse:
        """Executes prediction on customer features using the verified CatBoost pipeline with fixed 0.50 threshold."""
        model, canonical_model_name = self.get_model()
        cid = customer_id.strip() if customer_id and customer_id.strip() else f"CUST-{uuid.uuid4().hex[:8].upper()}"
        effective_threshold = self.FIXED_THRESHOLD

        # Convert pydantic features to DataFrame matching training format
        feat_dict = features.model_dump()
        input_df = pd.DataFrame([feat_dict])
        if "customerID" not in input_df.columns:
            input_df["customerID"] = cid

        # Run inference through CatBoost pipeline
        try:
            probabilities = model.predict_proba(input_df)[0]
            churn_prob = float(probabilities[1])
        except Exception as e:
            logger.error("Inference execution failed: %s", e)
            raise RuntimeError(f"Model prediction error: {str(e)}")

        # Classification decision based on fixed 0.50 threshold
        predicted_class = 1 if churn_prob >= effective_threshold else 0
        predicted_label = "Churn" if predicted_class == 1 else "No Churn"
        churn_pct = round(churn_prob * 100, 2)
        risk_level = self.calculate_risk_level(churn_prob)
        recommendation = self.generate_recommendation(risk_level, churn_prob, feat_dict)
        now = datetime.now(timezone.utc)

        prediction_id = None
        if save_to_db:
            db = get_database()
            doc = {
                "customer_id": cid,
                "customer_features": feat_dict,
                "predicted_class": predicted_class,
                "predicted_label": predicted_label,
                "churn_probability": churn_prob,
                "churn_percentage": churn_pct,
                "risk_level": risk_level,
                "model_name": canonical_model_name,
                "threshold": effective_threshold,
                "created_at": now,
            }
            res = await db.predictions.insert_one(doc)
            prediction_id = str(res.inserted_id)

        return PredictionResponse(
            prediction_id=prediction_id,
            customer_id=cid,
            predicted_class=predicted_class,
            predicted_label=predicted_label,
            churn_probability=round(churn_prob, 4),
            churn_percentage=churn_pct,
            risk_level=risk_level,
            model_name=canonical_model_name,
            threshold=effective_threshold,
            recommended_action=recommendation,
            created_at=now,
        )

    async def save_prediction(
        self,
        customer_id: str,
        customer_features: Dict[str, Any],
        predicted_class: int,
        churn_probability: float,
        risk_level: str,
        model_name: Optional[str] = None,
        threshold: Optional[float] = None,
    ) -> str:
        """Stores a prediction record in MongoDB with verified CatBoost metadata."""
        db = get_database()
        actual_model = model_name if model_name and "catboost" in model_name.lower() else self.MODEL_NAME
        actual_threshold = threshold if threshold is not None else self.FIXED_THRESHOLD
        doc = {
            "customer_id": customer_id,
            "customer_features": customer_features,
            "predicted_class": predicted_class,
            "predicted_label": "Churn" if predicted_class == 1 else "No Churn",
            "churn_probability": churn_probability,
            "churn_percentage": round(churn_probability * 100, 2),
            "risk_level": risk_level,
            "model_name": actual_model,
            "threshold": actual_threshold,
            "created_at": datetime.now(timezone.utc),
        }
        res = await db.predictions.insert_one(doc)
        return str(res.inserted_id)

    async def get_prediction_history(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        risk_level: Optional[str] = None,
    ) -> PredictionHistoryPagination:
        """Retrieves paginated and filtered prediction records."""
        db = get_database()
        query = {}

        if search and search.strip():
            query["customer_id"] = {"$regex": search.strip(), "$options": "i"}

        if risk_level and risk_level.strip():
            query["risk_level"] = risk_level.strip()

        total = await db.predictions.count_documents(query)
        total_pages = max(1, (total + page_size - 1) // page_size)
        skip = (page - 1) * page_size

        cursor = db.predictions.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        items = []
        async for doc in cursor:
            items.append(
                PredictionHistoryItem(
                    id=str(doc["_id"]),
                    _id=str(doc["_id"]),
                    customer_id=doc.get("customer_id", "Unknown"),
                    customer_features=doc.get("customer_features", {}),
                    predicted_class=doc.get("predicted_class", 0),
                    predicted_label=doc.get("predicted_label", "No Churn"),
                    churn_probability=doc.get("churn_probability", 0.0),
                    churn_percentage=doc.get("churn_percentage", 0.0),
                    risk_level=doc.get("risk_level", "Low Risk"),
                    model_name=doc.get("model_name", "Unknown"),
                    threshold=doc.get("threshold", 0.48),
                    created_at=doc.get("created_at", datetime.now(timezone.utc)),
                )
            )

        return PredictionHistoryPagination(
            items=items,
            predictions=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            pages=total_pages,
        )

    async def get_prediction_by_id(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        """Finds a single prediction document by its MongoDB ID."""
        db = get_database()
        try:
            oid = ObjectId(prediction_id)
        except Exception:
            return None
        doc = await db.predictions.find_one({"_id": oid})
        if doc:
            doc["id"] = str(doc["_id"])
        return doc

    async def delete_prediction(self, prediction_id: str) -> bool:
        """Deletes a prediction record by MongoDB ID."""
        db = get_database()
        try:
            oid = ObjectId(prediction_id)
        except Exception:
            return False
        res = await db.predictions.delete_one({"_id": oid})
        return res.deleted_count > 0

    async def export_history_csv(self) -> str:
        """Exports all predictions to a CSV format string."""
        db = get_database()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Prediction ID", "Customer ID", "Prediction Date", "Model Used",
            "Threshold", "Predicted Class", "Predicted Label", "Churn Probability", "Risk Level"
        ])

        cursor = db.predictions.find().sort("created_at", -1)
        async for doc in cursor:
            writer.writerow([
                str(doc["_id"]),
                doc.get("customer_id", ""),
                doc.get("created_at", ""),
                doc.get("model_name", ""),
                doc.get("threshold", 0.48),
                doc.get("predicted_class", 0),
                doc.get("predicted_label", ""),
                f"{doc.get('churn_probability', 0.0):.4f}",
                doc.get("risk_level", ""),
            ])

        return output.getvalue()


prediction_service = PredictionService()
