from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.datasets import router as datasets_router
from app.api.health import router as health_router
from app.api.analyst import router as analyst_router
from app.api.guardian import router as guardian_router
from app.services.data_loader import init_sample_datasets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize sample datasets on startup
    init_sample_datasets()
    yield

app = FastAPI(
    title="ProofGuard API",
    description="Independent Trust & Verification Layer for AI Data Analysis — Stages 1-4 Active",
    version="4.0.0",
    lifespan=lifespan
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(datasets_router, prefix="/api")
app.include_router(analyst_router, prefix="/api")
app.include_router(guardian_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "ProofGuard API - Stage 1 Foundation Online",
        "docs_url": "/docs",
        "status": "healthy"
    }
