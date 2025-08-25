from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Tuple
from fastapi.middleware.cors import CORSMiddleware

# --- Pydantic Models for Request and Response ---

class RouteRequest(BaseModel):
    start_point: Tuple[float, float]  # (latitude, longitude)
    end_point: Tuple[float, float]    # (latitude, longitude)

class RouteResponse(BaseModel):
    path: List[Tuple[float, float]] # A list of (lat, lon) points

# --- FastAPI Application ---

app = FastAPI(
    title="Shady Route API",
    description="API for finding the shadiest walking/cycling route in Paris.",
    version="0.1.0 (Proof of Concept)"
)

# --- CORS Middleware ---
# This allows the frontend (running on a different port) to make requests to this API.
origins = [
    "http://localhost",
    "http://localhost:8080", # The origin for our simple frontend server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """A simple root endpoint to check if the API is running."""
    return {"message": "Welcome to the Shady Route API!"}

@app.post("/api/route", response_model=RouteResponse)
def get_shady_route(request: RouteRequest):
    """
    Calculates the shadiest route between two points.

    **For this Proof of Concept, it returns a hardcoded dummy route.**
    """
    print(f"Received route request from {request.start_point} to {request.end_point}")

    # In the future, this will call the main() function from main.py
    # and return the real calculated path.

    # For now, return a dummy path that looks like a plausible route.
    dummy_path = [
        request.start_point,
        (48.858, 2.350), # A point in the middle
        (48.860, 2.345), # Another point
        request.end_point
    ]

    return {"path": dummy_path}

# To run this API, use the command:
# python3 -m uvicorn src.api:app --reload
