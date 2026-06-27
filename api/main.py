"""
FastAPI backend for Chitrabasha text classifier.

Run with:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import time

from src.inference import predict

app = FastAPI(
    title="Chitrabasha Text Classifier",
    description="Hybrid NB + LR + SVM text topic classifier with meta-model.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response schemas ────────────────────────────────────────────────

class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000, example="Python is great for machine learning")
    top_k: int = Field(default=3, ge=1, le=10)


class TopKItem(BaseModel):
    label: str
    score: float


class PredictResponse(BaseModel):
    label: str
    confidence: float
    top_k: list[TopKItem]
    model_votes: dict[str, str]
    decided_by: str
    latency_ms: float


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(req: PredictRequest):
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="Text must not be empty or whitespace.")

    t0     = time.perf_counter()
    result = predict(req.text, top_k=req.top_k)
    ms     = (time.perf_counter() - t0) * 1000

    return PredictResponse(
        label      = result["label"],
        confidence = result["confidence"],
        top_k      = [TopKItem(**item) for item in result["top_k"]],
        model_votes= result["model_votes"],
        decided_by = result["decided_by"],
        latency_ms = round(ms, 2),
    )