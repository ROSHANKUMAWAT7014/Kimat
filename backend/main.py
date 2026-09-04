"""
Kimat backend — FastAPI service serving the trained model + city/DB data.

    Frontend <-> Backend API <-> ML model, with Backend <-> Database

Run locally:
    uvicorn main:app --reload

Run in production (Render):
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import json
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.background import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Load .env before any module that reads env vars.
load_dotenv()

import ml_path  # noqa: F401  (inserts ml/ into sys.path so the imports below resolve)
from city_data import CITIES
from predict import PricePredictor
from drivers import compute_drivers, city_trend, _age_band_and_mult

from database import get_logs_collection, get_stats_collection, get_user_collection
from schemas import (
    CityStatsOut,
    CompareModelsResponse,
    PredictRequest,
    PredictResponse,
    PriceTrendResponse,
    TrendPoint,
    UserCreate,
    UserLogin,
    UserOut,
    Token,
)
from auth import verify_password, get_password_hash, create_access_token, verify_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kimat")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Set FRONTEND_URL in the environment to restrict origins in production.
# Example production value: https://your-app.vercel.app
# Multiple origins can be specified as a comma-separated list:
#   FRONTEND_URL=https://your-app.vercel.app,https://your-custom-domain.com
# ---------------------------------------------------------------------------
_raw_origins = os.environ.get("FRONTEND_URL", "http://localhost:3000,http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app = FastAPI(
    title="Kimat API",
    description="India house price prediction",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Model lifecycle
# ---------------------------------------------------------------------------
predictor: PricePredictor | None = None


@app.on_event("startup")
def startup() -> None:
    global predictor
    try:
        predictor = PricePredictor()
        logger.info("Loaded model: %s", predictor.model_name)
    except FileNotFoundError as exc:
        logger.warning(
            "No trained model found — run `python train.py` inside ml/ first. "
            "/predict will return 503 until a model is loaded. Detail: %s",
            exc,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _log_prediction(
    logs_collection,
    specs: dict,
    result: dict,
    client_ip: str,
) -> None:
    try:
        logs_collection.insert_one(
            {
                "created_at": datetime.now(timezone.utc),
                "city": specs["city"],
                "locality": specs["locality"],
                "area_sqft": specs["area_sqft"],
                "bhk": specs["bhk"],
                "bathrooms": specs["bathrooms"],
                "floor": specs["floor"],
                "total_floors": specs["total_floors"],
                "property_age_years": specs["property_age_years"],
                "furnishing_status": specs["furnishing_status"],
                "property_type": specs["property_type"],
                "amenities_csv": ",".join(specs.get("amenities", [])),
                "predicted_price": result["price"],
                "price_low": result["low"],
                "price_high": result["high"],
                "model_used": result["model_used"],
                "client_ip": client_ip,
            }
        )
    except Exception:
        logger.exception("Failed to log prediction (non-fatal, response already sent)")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """Liveness probe — used by Render and monitoring tools."""
    return {"status": "ok", "model_loaded": predictor is not None}


@app.post("/predict", response_model=PredictResponse)
def predict(
    req: PredictRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    logs_collection=Depends(get_logs_collection),
):
    if predictor is None:
        raise HTTPException(503, "Model not loaded — run `python train.py` in ml/ first.")

    specs = req.model_dump()
    age_band, _ = _age_band_and_mult(specs["property_age_years"])

    model_input = {
        "city": specs["city"],
        "locality": specs["locality"],
        "area_sqft": specs["area_sqft"],
        "bhk": specs["bhk"],
        "bathrooms": specs["bathrooms"],
        "floor": specs["floor"],
        "total_floors": specs["total_floors"],
        "property_age_years": specs["property_age_years"],
        "age_band": age_band,
        "furnishing_status": specs["furnishing_status"],
        "property_type": specs["property_type"],
        **{
            a: (1 if a in specs["amenities"] else 0)
            for a in ["parking", "lift", "security", "power_backup", "gym", "pool", "clubhouse", "garden"]
        },
    }

    result = predictor.predict(model_input)
    drivers = compute_drivers(model_input)
    city_base_rate = CITIES[specs["city"]]["base_rate"]

    response = PredictResponse(
        price=result["price"],
        low=result["low"],
        high=result["high"],
        per_sqft=result["per_sqft"],
        city_base_rate=city_base_rate,
        confidence_band_pct=result["confidence_band_pct"],
        model_used=result["model_used"],
        drivers=drivers,
    )

    client_ip = request.client.host if request.client else ""
    background_tasks.add_task(_log_prediction, logs_collection, specs, result, client_ip)

    return response


@app.get("/compare-models", response_model=CompareModelsResponse)
def compare_models():
    metrics_path = ml_path.ML_DIR / "models" / "metrics.json"
    if not metrics_path.exists():
        raise HTTPException(503, "No metrics found — run `python train.py` in ml/ first.")
    return json.loads(metrics_path.read_text())


@app.get("/city-stats", response_model=list[CityStatsOut])
def city_stats(stats_collection=Depends(get_stats_collection)):
    rows = list(stats_collection.find())
    if not rows:
        raise HTTPException(
            503,
            "No city stats cached — run `python seed_db.py` in backend/ first.",
        )
    return [
        CityStatsOut(
            city=r["city"],
            name=CITIES.get(r["city"], {}).get("name", r["city"].title()),
            state=r["state"],
            avg_price_per_sqft=r["avg_price_per_sqft"],
            yoy_growth_pct=r["yoy_growth_pct"],
            locality_count=r["locality_count"],
            listing_count=r["listing_count"],
        )
        for r in rows
    ]


@app.get("/price-trends", response_model=PriceTrendResponse)
def price_trends(city: str):
    if city not in CITIES:
        raise HTTPException(404, f"Unknown city '{city}'. Valid: {list(CITIES.keys())}")
    points = [TrendPoint(**p) for p in city_trend(city)]
    return PriceTrendResponse(city=city, points=points)


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.post("/api/auth/signup", response_model=Token)
def signup(
    user_data: UserCreate,
    users_collection=Depends(get_user_collection),
):
    normalized_email = user_data.email.strip().lower()
    if users_collection.find_one({"email": normalized_email}):
        raise HTTPException(
            status_code=400,
            detail="This email is already registered. Please log in instead.",
        )

    hashed_password = get_password_hash(user_data.password)
    now = datetime.now(timezone.utc)
    new_user = {
        "full_name": user_data.full_name,
        "email": normalized_email,
        "password_hash": hashed_password,
        "created_at": now,
        "updated_at": now,
    }
    users_collection.insert_one(new_user)

    access_token = create_access_token(data={"sub": normalized_email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=Token)
def login(
    user_data: UserLogin,
    users_collection=Depends(get_user_collection),
):
    normalized_email = user_data.email.strip().lower()
    user = users_collection.find_one({"email": normalized_email})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    access_token = create_access_token(data={"sub": normalized_email})
    return {"access_token": access_token, "token_type": "bearer"}


security = HTTPBearer()


@app.get("/api/auth/me", response_model=UserOut)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    users_collection=Depends(get_user_collection),
):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user = users_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    return UserOut(
        id=str(user["_id"]),
        full_name=user["full_name"],
        email=user["email"],
    )
