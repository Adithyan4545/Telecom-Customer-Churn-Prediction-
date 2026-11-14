"""Inference and prediction record management endpoints."""

from fastapi import APIRouter, HTTPException, Query, status, Response
from backend.app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    SavePredictionRequest,
    PredictionHistoryPagination,
)
from backend.app.services.prediction_service import prediction_service

router = APIRouter(tags=["Prediction"])


@router.post("/predict", response_model=PredictionResponse)
async def predict_churn(request: PredictionRequest):
    """Executes churn prediction on customer attributes using the active CatBoost pipeline."""
    try:
        return await prediction_service.predict_churn(
            features=request.features,
            customer_id=request.customer_id,
            save_to_db=request.save_to_db or False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictions", status_code=status.HTTP_201_CREATED)
async def save_prediction_record(request: SavePredictionRequest):
    """Saves a prediction result to MongoDB."""
    try:
        pid = await prediction_service.save_prediction(
            customer_id=request.customer_id,
            customer_features=request.customer_features,
            predicted_class=request.predicted_class,
            churn_probability=request.churn_probability,
            risk_level=request.risk_level,
            model_name=request.model_name,
            threshold=request.threshold,
        )
        return {"id": pid, "message": "Prediction saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions", response_model=PredictionHistoryPagination)
async def list_predictions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str = Query(None, description="Search by customer ID"),
    risk_level: str = Query(None, description="Filter by risk level"),
):
    """Lists saved predictions with pagination and filtering."""
    return await prediction_service.get_prediction_history(
        page=page,
        page_size=page_size,
        search=search,
        risk_level=risk_level,
    )


@router.get("/predictions/export/csv")
async def export_predictions_csv():
    """Exports prediction history to downloadable CSV file."""
    csv_content = await prediction_service.export_history_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=churn_predictions_export.csv"},
    )


@router.get("/predictions/{prediction_id}")
async def get_prediction_record(prediction_id: str):
    """Retrieves an individual prediction record by ID."""
    doc = await prediction_service.get_prediction_by_id(prediction_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Prediction record not found")
    return doc


@router.delete("/predictions/{prediction_id}")
async def delete_prediction_record(prediction_id: str):
    """Deletes an individual prediction record by ID."""
    success = await prediction_service.delete_prediction(prediction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prediction record not found or could not be deleted")
    return {"message": "Prediction deleted successfully", "id": prediction_id}
