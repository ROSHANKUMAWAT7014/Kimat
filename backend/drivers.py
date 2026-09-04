"""
Per-request "what's driving this price" breakdown, and the 12-month trend
series. Ported from src/lib/kimat/model.ts so the plain-language explanation
matches what the frontend already shows, regardless of which trained model
produced the point estimate.
"""

import math

import ml_path  # noqa: F401
from city_data import CITIES, TYPE_MULT, FURNISH_MULT, AGE_BANDS, AMENITIES

MONTHS = ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
SEASONAL = [-0.004, 0.006, 0.011, 0.004, -0.006, 0.002, 0.009, 0.005, -0.002, 0.001, 0.004, 0.007]


def _age_band_and_mult(years: int):
    for band, (lo, hi, mult) in AGE_BANDS.items():
        if lo <= years < hi or (band == "20+" and years >= 20):
            return band, mult
    return "20+", AGE_BANDS["20+"][2]


def _floor_mult(property_type, floor, total_floors):
    if property_type == "plot":
        return 1.0
    ratio = floor / total_floors if total_floors > 0 else 0
    height = min(floor, 40) * 0.0042
    penthouse = 0.018 if ratio > 0.85 else 0
    ground = -0.03 if floor == 0 else 0
    return 1 + height + penthouse + ground


def _config_mult(area, bhk, bathrooms):
    expected_bhk = max(1, round(area / 460))
    delta = bhk - expected_bhk
    bath_delta = bathrooms - max(1, bhk - 1)
    return 1 + delta * 0.022 + bath_delta * 0.017


def _scale_mult(area):
    return math.pow(area / 1000, -0.045)


def compute_drivers(specs: dict) -> list[dict]:
    """Returns the diverging-bar breakdown for the DriversPanel, sorted by |impact|."""
    city = CITIES[specs["city"]]
    loc_mult = city["localities"][specs["locality"]]
    age_band, age_mult = _age_band_and_mult(specs["property_age_years"])
    amenity_bonus = sum(w for k, w in AMENITIES.items() if specs.get(k))

    factors = [
        ("locality", "Locality", loc_mult, f"{specs['locality']} vs. city average"),
        ("type", "Property type", TYPE_MULT[specs["property_type"]], f"{specs['property_type']} stock"),
        ("furnishing", "Furnishing", FURNISH_MULT[specs["furnishing_status"]],
         {"full": "Fully furnished units resell higher",
          "semi": "Semi-furnished — modest lift",
          "unfurnished": "Unfurnished baseline"}[specs["furnishing_status"]]),
        ("age", "Property age", age_mult,
         "Newer construction commands a premium" if age_band in ("new", "1-5")
         else "Older stock depreciates against new launches"),
        ("floor", "Floor position", _floor_mult(specs["property_type"], specs["floor"], specs["total_floors"]),
         f"Floor {specs['floor']} of {specs['total_floors']}"),
        ("config", "Configuration", _config_mult(specs["area_sqft"], specs["bhk"], specs["bathrooms"]),
         f"{specs['bhk']} BHK · {specs['bathrooms']} bath for {specs['area_sqft']} sq.ft"),
        ("amenities", "Amenities", 1 + amenity_bonus,
         f"{sum(1 for k in AMENITIES if specs.get(k))} amenities selected"),
        ("scale", "Unit size effect", _scale_mult(specs["area_sqft"]),
         "Larger units price lower per sq.ft" if specs["area_sqft"] > 1000 else "Compact unit premium"),
    ]

    drivers = [
        {"key": k, "label": label, "impact_pct": round((val - 1) * 100, 2), "note": note}
        for k, label, val, note in factors
    ]
    drivers.sort(key=lambda d: abs(d["impact_pct"]), reverse=True)
    return drivers


def city_trend(city_id: str) -> list[dict]:
    """Deterministic 12-month rate-per-sqft series, same formula as the frontend."""
    city = CITIES[city_id]
    monthly = city["yoy"] / 12
    points = []
    for i, m in enumerate(MONTHS):
        steps_back = len(MONTHS) - 1 - i
        drift = (1 + monthly) ** (-steps_back)
        points.append({"month": m, "rate": round(city["base_rate"] * drift * (1 + SEASONAL[i]))})
    return points
