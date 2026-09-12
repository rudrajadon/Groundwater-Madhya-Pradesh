import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import forecast, wells, zones, location_predictor, stress_map, exports, districts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the ML model at startup so it's available for all requests.
    Graph structure (node features + adjacency matrix) is now loaded
    directly by the ForecastModel from pre-built artifacts."""
    print("[startup] Backend starting...")
    
    # Test database connection
    try:
        from sqlalchemy import text
        from .db import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("[startup] Database connection OK")
    except Exception as e:
        print(f"[startup] WARNING: Database connection failed: {e}")
        print("[startup] Continuing anyway - /health endpoint will still work")
    
    # SKIP ML model loading - we use cached forecasts now!
    # Model is 500MB+ and exceeds Render free tier memory (512MB)
    # All 1,011 wells have pre-calculated forecasts in forecast_cache
    app.state.model = None
    print(f"[startup] ML model loading DISABLED - using cached forecasts only")
    print(f"[startup] 1,011+ wells have pre-calculated forecasts in database")
    
    print("[startup] Backend ready!")
    yield
    print("[shutdown] Backend shutting down...")


app = FastAPI(title="Indore Groundwater Forecast API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the deployed frontend origin before going live
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wells.router)
app.include_router(forecast.router)
app.include_router(zones.router)
app.include_router(location_predictor.router)
app.include_router(stress_map.router)
app.include_router(exports.router)
app.include_router(districts.router)


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": hasattr(app.state, "model") and app.state.model is not None}
