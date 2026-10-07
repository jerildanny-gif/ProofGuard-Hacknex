from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check():
    return {
        "status": "online",
        "service": "ProofGuard Verification Engine - Stage 1 Foundation",
        "stage": 1,
        "capabilities": [
            "csv_xlsx_upload",
            "dataset_preview",
            "column_type_inference",
            "summary_statistics",
            "anomaly_and_messy_data_detection",
            "sample_datasets"
        ]
    }
