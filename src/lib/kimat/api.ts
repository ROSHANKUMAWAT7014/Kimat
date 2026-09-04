/**
 * Kimat API client — talks to the FastAPI backend.
 *
 * The base URL is controlled by the VITE_API_URL environment variable.
 * Set it in a root-level .env file:
 *
 *   VITE_API_URL=http://localhost:8000      ← local dev
 *   VITE_API_URL=https://your-app.onrender.com  ← production
 *
 * If VITE_API_URL is not set the client defaults to http://localhost:8000
 * so local dev works without any configuration.
 */

import type { AmenityKey, Driver, Furnishing, PropertyType, Specs } from "./model";
import { predict as localPredict } from "./model";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types that mirror the FastAPI response schemas
// ---------------------------------------------------------------------------

export interface ApiPredictResponse {
  price: number;
  low: number;
  high: number;
  per_sqft: number;
  city_base_rate: number;
  confidence_band_pct: number;
  model_used: string;
  drivers: {
    key: string;
    label: string;
    impact_pct: number;
    note: string;
  }[];
}

// ---------------------------------------------------------------------------
// Map frontend Specs → backend PredictRequest payload
// ---------------------------------------------------------------------------

/** Maps AgeBand string label to a property_age_years midpoint for the API. */
const AGE_BAND_TO_YEARS: Record<string, number> = {
  new: 0,
  "1-5": 3,
  "5-10": 7,
  "10-20": 15,
  "20+": 25,
};

/**
 * Maps the backend amenity key names.
 * The frontend uses "power" but the backend expects "power_backup".
 */
const AMENITY_KEY_MAP: Partial<Record<AmenityKey, string>> = {
  power: "power_backup",
};

function mapAmenity(key: AmenityKey): string {
  return AMENITY_KEY_MAP[key] ?? key;
}

function specsToPayload(specs: Specs) {
  return {
    city: specs.cityId,
    locality: specs.locality,
    area_sqft: specs.area,
    bhk: specs.bhk,
    bathrooms: specs.bathrooms,
    floor: specs.floor,
    total_floors: specs.totalFloors,
    property_age_years: AGE_BAND_TO_YEARS[specs.age] ?? 3,
    furnishing_status: specs.furnishing as Furnishing,
    property_type: specs.propertyType as PropertyType,
    amenities: specs.amenities.map(mapAmenity),
  };
}

// ---------------------------------------------------------------------------
// API call
// ---------------------------------------------------------------------------

/**
 * POST /predict — returns the backend prediction.
 * Throws on network / non-2xx errors so callers can handle gracefully.
 */
export async function fetchPrediction(specs: Specs): Promise<ApiPredictResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(specsToPayload(specs)),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(detail.detail ?? `Backend error ${res.status}`);
  }

  return res.json() as Promise<ApiPredictResponse>;
}

// ---------------------------------------------------------------------------
// Normalise API response → frontend Prediction shape
// ---------------------------------------------------------------------------

/**
 * Convert an ApiPredictResponse into the same shape the local predict()
 * returns so all existing components (EstimateCard, DriversPanel, etc.)
 * keep working without modification.
 */
export function apiResponseToPrediction(
  api: ApiPredictResponse,
  specs: Specs,
): ReturnType<typeof localPredict> {
  const drivers: Driver[] = api.drivers.map((d) => ({
    key: d.key,
    label: d.label,
    impact: d.impact_pct,   // backend calls it impact_pct; frontend calls it impact
    note: d.note,
  }));

  return {
    price: api.price,
    low: api.low,
    high: api.high,
    perSqft: api.per_sqft,
    cityBaseRate: api.city_base_rate,
    drivers,
    confidence: api.confidence_band_pct / 100,
  };
}
