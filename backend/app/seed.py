"""Database initialization and seeding script.

Creates the default administrator account and populates sample customer/prediction records.
Usage:
    python backend/app/seed.py
"""

import sys
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
from pymongo import MongoClient

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings
from backend.app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("seed")


def seed_database():
    logger.info("Starting database seeding process...")
    client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
    db = client[settings.DATABASE_NAME]

    # 1. Seed Administrator Account
    admin_user = db.users.find_one({"email": settings.ADMIN_EMAIL})
    if not admin_user:
        hashed_pw = get_password_hash(settings.ADMIN_PASSWORD)
        db.users.insert_one({
            "name": settings.ADMIN_NAME,
            "email": settings.ADMIN_EMAIL,
            "hashed_password": hashed_pw,
            "role": "admin",
            "created_at": datetime.now(timezone.utc),
        })
        logger.info("Admin account created: %s (Password: %s)", settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD)
    else:
        logger.info("Admin account already exists: %s", settings.ADMIN_EMAIL)

    # 2. Seed Initial Prediction History if empty
    pred_count = db.predictions.count_documents({})
    if pred_count == 0 and settings.DATASET_PATH.exists():
        logger.info("Seeding initial prediction records from dataset sample...")
        df = pd.read_csv(settings.DATASET_PATH)
        sample_customers = df.iloc[:15].copy()

        now = datetime.now(timezone.utc)
        sample_preds = []
        for idx, row in sample_customers.iterrows():
            cid = str(row["customerID"])
            actual = str(row["Churn"])
            is_churn = actual == "Yes"

            # Assign realistic probability based on ground truth
            prob = 0.78 + (idx % 4) * 0.04 if is_churn else 0.12 + (idx % 6) * 0.04
            prob = min(0.96, max(0.04, prob))
            risk_level = "High Risk" if prob >= 0.70 else ("Medium Risk" if prob >= 0.40 else "Low Risk")
            predicted_class = 1 if prob >= 0.48 else 0

            feat_dict = row.to_dict()
            feat_dict.pop("customerID", None)
            feat_dict.pop("Churn", None)

            sample_preds.append({
                "customer_id": cid,
                "customer_features": feat_dict,
                "predicted_class": predicted_class,
                "predicted_label": "Churn" if predicted_class == 1 else "No Churn",
                "churn_probability": round(prob, 4),
                "churn_percentage": round(prob * 100, 2),
                "risk_level": risk_level,
                "model_name": "Optimized Stacking Classifier",
                "threshold": 0.48,
                "created_at": now - timedelta(days=idx, hours=idx * 2),
            })

        db.predictions.insert_many(sample_preds)
        logger.info("Successfully seeded %d initial prediction records.", len(sample_preds))
    else:
        logger.info("Database already contains %d prediction records.", pred_count)

    logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    seed_database()
