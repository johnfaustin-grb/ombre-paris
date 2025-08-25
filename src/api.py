from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta
import logging

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler() # Also print to console
    ]
)

# Use relative import to import from within the same package
from .main import find_shady_path

# --- Pydantic Models ---
class RouteRequest(BaseModel):
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]

class RouteResponse(BaseModel):
    path: List[Tuple[float, float]]

# --- FastAPI Application ---
app = FastAPI(title="Shady Route API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Shady Route API!"}

@app.post("/api/route", response_model=RouteResponse)
def get_shady_route(request: RouteRequest):
    logging.info(f"Received REAL route request from {request.start_point} to {request.end_point}")

    paris_tz = timezone(timedelta(hours=2))
    calculation_time = datetime(2025, 8, 25, 14, 0, 0, tzinfo=paris_tz)

    try:
        path_coords = find_shady_path(request.start_point, request.end_point, calculation_time)

        if path_coords is None:
            logging.warning("No path could be found between the specified points.")
            raise HTTPException(status_code=404, detail="Could not find a path.")

        logging.info(f"Successfully found a path with {len(path_coords)} points.")
        return {"path": path_coords}
    except Exception as e:
        logging.error(f"An unexpected error occurred during route calculation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred.")
