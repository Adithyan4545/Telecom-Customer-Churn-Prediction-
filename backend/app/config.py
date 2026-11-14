"""Application configuration and environment settings."""

import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Server, database, security, and machine learning configuration."""

    PROJECT_NAME: str = "Telecom Customer Churn Prediction System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "telecom_churn"

    # Security & JWT
    JWT_SECRET: str = "super-secret-telecom-jwt-key-for-development-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Initial Administrator Account
    ADMIN_NAME: str = "System Administrator"
    ADMIN_EMAIL: str = "admin@telecom.com"
    ADMIN_PASSWORD: str = "admin123"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*",
    ]

    # File Paths
    DATASET_PATH: Path = BASE_DIR / "dataset" / "Telco-Customer-Churn.csv"
    CATBOOST_MODEL_PATH: Path = (
        BASE_DIR / "experiments" / "accuracy_optimization" / "best_accuracy_pipeline.pkl"
    )
    ALT_MODEL_PATH: Path = BASE_DIR / "models" / "best_accuracy_pipeline.pkl"
    EXPERIMENT_SUMMARY_PATH: Path = (
        BASE_DIR / "experiments" / "accuracy_optimization" / "experiment_summary.json"
    )
    MODEL_METADATA_PATH: Path = BASE_DIR / "models" / "model_metadata.json"
    OUTPUTS_DIR: Path = BASE_DIR / "outputs"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
