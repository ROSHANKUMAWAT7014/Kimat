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

import type { AmenityKey, Driver, Furnishing, Prediction, PropertyType, Specs } from "./model";
import { getLocalities, LOCATION_TO_CITY_ID } from "@/data/indiaLocations";

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

function isValidPredictionSpecs(specs: Specs) {
  const validNumbers = [
    specs.area,
    specs.bhk,
    specs.bathrooms,
    specs.floor,
    specs.totalFloors,
  ].every((value) => Number.isFinite(value));
  const validLocation =
    Boolean(specs.state && specs.district && specs.city && specs.locality) &&
    Boolean(LOCATION_TO_CITY_ID[specs.city]) &&
    specs.cityId === LOCATION_TO_CITY_ID[specs.city] &&
    getLocalities(specs.state, specs.district, specs.city).includes(specs.locality);

  return (
    validLocation &&
    validNumbers &&
    specs.area > 0 &&
    specs.bhk >= 1 &&
    specs.bathrooms >= 1 &&
    specs.floor >= 0 &&
    specs.totalFloors >= 0
  );
}

function validatePredictionValues(prediction: Prediction) {
  const values = [prediction.price, prediction.low, prediction.high, prediction.perSqft];
  if (values.some((value) => !Number.isFinite(value) || value < 0)) {
    throw new Error("The prediction returned invalid price values. Please try again.");
  }
}

function formatApiDetail(detail: unknown) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== "object") return null;
        const message = "msg" in item ? item.msg : null;
        return typeof message === "string" ? message : null;
      })
      .filter((message): message is string => message !== null);

    if (messages.length > 0) {
      const summary = "Invalid property location. Please select a supported city and locality.";
      return import.meta.env.DEV ? `${summary} (${messages.join("; ")})` : summary;
    }
  }
  return undefined;
}

// ---------------------------------------------------------------------------
// API call
// ---------------------------------------------------------------------------

/**
 * POST /predict — returns the backend prediction.
 * Throws on network / non-2xx errors so callers can handle gracefully.
 */
export async function fetchPrediction(specs: Specs): Promise<ApiPredictResponse> {
  if (!isValidPredictionSpecs(specs)) {
    throw new Error("Invalid property location or prediction inputs. Please select a supported city and locality.");
  }

  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(specsToPayload(specs)),
  });

  if (!res.ok) {
    const body: unknown = await res.json().catch(() => null);
    const detail = body && typeof body === "object" && "detail" in body ? body.detail : undefined;
    throw new Error(formatApiDetail(detail) ?? `Backend error ${res.status}`);
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
): Prediction {
  const drivers: Driver[] = api.drivers.map((d) => ({
    key: d.key,
    label: d.label,
    impact: d.impact_pct,   // backend calls it impact_pct; frontend calls it impact
    note: d.note,
  }));

  const prediction = {
    price: api.price,
    low: api.low,
    high: api.high,
    perSqft: api.per_sqft,
    cityBaseRate: api.city_base_rate,
    drivers,
    confidence: api.confidence_band_pct / 100,
  };

  validatePredictionValues(prediction);
  return prediction;
}
