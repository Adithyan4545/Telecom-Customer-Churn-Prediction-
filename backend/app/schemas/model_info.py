"""Model metadata and feature importance schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class FeatureImportanceItem(BaseModel):
    feature: str
    display_name: str
    importance: float
    description: str


class ModelInfoResponse(BaseModel):
    model_name: str
    algorithm: str
    dataset_records: int
    training_approach: str
    preprocessing_steps: List[str]
    feature_engineering_techniques: List[str]
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    pr_auc: Optional[float] = None
    confusion_matrix: Dict[str, int]
    top_features: List[FeatureImportanceItem]
