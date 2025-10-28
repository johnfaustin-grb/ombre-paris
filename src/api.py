from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timezone, timedelta
import logging
from contextlib import asynccontextmanager

# Use relative import to import from within the same package
from .main import find_shady_path, load_graph

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    logging.info("API Startup: Loading street graph into memory...")
    success = load_graph()
    if not success:
        logging.error("CRITICAL: Could not load street graph. The API will not be able to find routes.")
    yield
    # This code runs on shutdown (if any cleanup were needed)
    logging.info("API Shutdown.")

# --- FastAPI Application ---
app = FastAPI(
    title="Shady Route API",
    version="1.2.0 (Pre-processed Data)",
    lifespan=lifespan
)

# --- API Models ---
class RouteRequest(BaseModel):
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]

class RouteResponse(BaseModel):
    path: List[Tuple[float, float]]

# --- API Routes ---
@app.post("/api/route", response_model=RouteResponse)
def get_shady_route(request: RouteRequest):
    logging.info(f"Received route request from {request.start_point} to {request.end_point}")

    paris_tz = timezone(timedelta(hours=2))
    calculation_time = datetime(2025, 8, 25, 14, 0, 0, tzinfo=paris_tz)

    try:
        path_coords = find_shady_path(request.start_point, request.end_point, calculation_time)
        if path_coords is None:
            raise HTTPException(status_code=404, detail="Could not find a path.")
        return {"path": path_coords}
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

# --- Static Files (Frontend) ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
