"""Production-ready HTTP API for the synthetic ECG signal analyzer."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ecg_analyzer import analyze_ecg



logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("ecg_api")
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_PAGE = BASE_DIR / "frontend" / "index.html"


class AnalysisRequest(BaseModel):
    """Parameters for generating a synthetic ECG waveform."""

    sampling_rate: int = Field(default=250, ge=50, le=2_000, description="Samples per second")
    duration: float = Field(default=10, gt=0, le=120, description="Signal duration in seconds")
    noise_level: float = Field(default=0.5, ge=0, le=5, description="Random-noise amplitude")
    heart_rate: float = Field(default=72, ge=30, le=240, description="Target heart rate in BPM")
    seed: int | None = Field(default=None, description="Optional seed for repeatable noise")


allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
    if origin.strip()
]

app = FastAPI(
    title="ECG Signal Analyzer API",
    description=(
        "Generates and analyzes synthetic ECG-like signals with SciPy. "
        "This application is educational only and must not be used for medical diagnosis."
    ),
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception) -> JSONResponse:
    """Log unexpected errors without exposing internal details to clients."""
    logger.exception("Unexpected API error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": "Analysis failed. Please try again."})


@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
async def dashboard() -> FileResponse:
    """Serve the browser dashboard."""
    return FileResponse(FRONTEND_PAGE, media_type="text/html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Empty favicon response to prevent 404 logs."""
    return Response(status_code=204)


@app.get("/health", tags=["service"])
async def health_check() -> dict[str, str]:
    """Health-check endpoint for hosting platforms and load balancers."""
    return {"status": "ok", "service": "ecg-signal-analyzer"}


@app.get("/analyze", tags=["analysis"])
@app.post("/analyze", tags=["analysis"])
async def analyze(request: AnalysisRequest = AnalysisRequest()) -> dict:
    """Generate, filter, and analyze a synthetic ECG waveform."""
    try:
        return analyze_ecg(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

