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
    
    # Try to load ML model (optional)
    model_dir = os.environ.get("MODEL_ARTIFACT_DIR", "../ml/artifacts")
    model_meta_path = os.path.join(model_dir, "model_metadata.json")
    if os.path.exists(model_meta_path):
        try:
            import sys
            ml_dir = os.path.abspath(os.path.join(model_dir, ".."))
            if ml_dir not in sys.path:
                sys.path.insert(0, ml_dir)
            from inference import ForecastModel
            
            app.state.model = ForecastModel(model_dir)
            print(f"[startup] Loaded model from {model_dir}")
            
            if hasattr(app.state.model, '_node_feat') and app.state.model._node_feat is not None:
                print(f"[startup] Graph loaded: {app.state.model._node_feat.shape[0]} wells")
            else:
                print(f"[startup] WARNING: Graph not loaded - predictions will be poor!")
        except Exception as e:
            print(f"[startup] WARNING: Model loading failed: {e}")
            app.state.model = None
    else:
        app.state.model = None
        print(f"[startup] No model artifact at {model_meta_path} — forecast endpoint will return 503")
    
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
