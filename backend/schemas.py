from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

# --- AUTH SCHEMAS ---
class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=1)
    email: str
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: str
    full_name: str
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
# --------------------

import ml_path  # noqa: F401  (sets sys.path before the import below)
from city_data import CITIES, PROPERTY_TYPES, FURNISHING_STATUSES, AMENITY_KEYS

PropertyType = Literal["apartment", "villa", "independent", "plot"]
Furnishing = Literal["unfurnished", "semi", "full"]
AmenityKey = Literal["parking", "lift", "security", "power_backup", "gym", "pool", "clubhouse", "garden"]


class PredictRequest(BaseModel):
    city: str = Field(..., description=f"One of: {', '.join(CITIES.keys())}")
    locality: str
    area_sqft: float = Field(..., ge=200, le=10000)
    bhk: int = Field(..., ge=1, le=6)
    bathrooms: int = Field(..., ge=1, le=8)
    floor: int = Field(..., ge=0, le=60)
    total_floors: int = Field(..., ge=0, le=60)
    property_age_years: int = Field(..., ge=0, le=60)
    furnishing_status: Furnishing
    property_type: PropertyType
    amenities: List[AmenityKey] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_consistency(self):
        if self.city not in CITIES:
            raise ValueError(f"Unknown city '{self.city}'. Valid cities: {list(CITIES.keys())}")

        valid_localities = CITIES[self.city]["localities"]
        if self.locality not in valid_localities:
            raise ValueError(
                f"Unknown locality '{self.locality}' for city '{self.city}'. "
                f"Valid localities: {list(valid_localities.keys())}"
            )

        if self.property_type != "plot" and self.floor > self.total_floors:
            raise ValueError("floor cannot exceed total_floors")

        if self.bathrooms > self.bhk + 2:
            raise ValueError("bathrooms looks inconsistent with bhk (max bhk + 2)")

        return self


class DriverOut(BaseModel):
    key: str
    label: str
    impact_pct: float
    note: str


class PredictResponse(BaseModel):
    price: float
    low: float
    high: float
    per_sqft: float
    city_base_rate: float
    confidence_band_pct: float
    model_used: str
    drivers: List[DriverOut]


class ModelMetrics(BaseModel):
    rmse: float
    mae: float
    r2: float
    train_seconds: float


class CompareModelsResponse(BaseModel):
    results: dict[str, ModelMetrics]
    best_model: str


class CityStatsOut(BaseModel):
    city: str
    name: str
    state: str
    avg_price_per_sqft: float
    yoy_growth_pct: float
    locality_count: int
    listing_count: int


class TrendPoint(BaseModel):
    month: str
    rate: float


class PriceTrendResponse(BaseModel):
    city: str
    points: List[TrendPoint]
