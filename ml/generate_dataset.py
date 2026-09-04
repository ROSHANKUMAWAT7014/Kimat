"""
Generate a synthetic India housing dataset.

WHY SYNTHETIC: this sandbox has no internet access, so real listings
(Kaggle / MagicBricks / 99acres exports) can't be downloaded here. Rather
than ship a tiny hand-typed CSV, this script generates ~18,000 realistic
listings using the same city/locality/amenity rate structure already
live in the frontend (ml/city_data.py, ported from src/lib/kimat/model.ts),
plus:
  - Gaussian pricing noise (real listings never fit a formula exactly)
  - Correlated-but-imperfect BHK/area/bathroom relationships
  - ~3% missing values sprinkled into a few columns
  - ~1.5% injected outliers (data-entry style errors)
so the preprocessing/cleaning step has real work to do.

To swap in a real dataset later: produce a CSV with the same columns
(see data_dictionary.md) and point preprocessing.py at it instead.
"""

import numpy as np
import pandas as pd
from city_data import (
    CITIES, TYPE_MULT, FURNISH_MULT, AGE_BANDS, AMENITIES,
    PROPERTY_TYPES, FURNISHING_STATUSES, AGE_BAND_LABELS, AMENITY_KEYS,
)

RNG = np.random.default_rng(42)
N_ROWS = 18000


def sample_age():
    band = RNG.choice(AGE_BAND_LABELS, p=[0.12, 0.28, 0.24, 0.22, 0.14])
    lo, hi, mult = AGE_BANDS[band]
    years = RNG.integers(lo, max(hi, lo + 1))
    return band, years, mult


def config_mult(area, bhk, bathrooms):
    expected_bhk = max(1, round(area / 460))
    delta = bhk - expected_bhk
    bath_delta = bathrooms - max(1, bhk - 1)
    return 1 + delta * 0.022 + bath_delta * 0.017


def floor_mult(property_type, floor, total_floors):
    if property_type == "plot":
        return 1.0
    ratio = floor / total_floors if total_floors > 0 else 0
    height = min(floor, 40) * 0.0042
    penthouse = 0.018 if ratio > 0.85 else 0
    ground = -0.03 if floor == 0 else 0
    return 1 + height + penthouse + ground


def scale_mult(area):
    return (area / 1000) ** -0.045


def gen_row():
    city_id = RNG.choice(list(CITIES.keys()))
    city = CITIES[city_id]
    locality, loc_mult = list(city["localities"].items())[
        RNG.integers(0, len(city["localities"]))
    ]

    property_type = RNG.choice(PROPERTY_TYPES, p=[0.62, 0.10, 0.18, 0.10])
    bhk = int(RNG.choice([1, 2, 3, 4, 5], p=[0.12, 0.34, 0.34, 0.15, 0.05]))
    area_center = 380 + bhk * 340
    area = float(np.clip(RNG.normal(area_center, area_center * 0.18), 250, 8000))
    bathrooms = int(np.clip(bhk - RNG.integers(0, 2), 1, bhk + 1))

    if property_type == "plot":
        total_floors, floor = 0, 0
    else:
        total_floors = int(np.clip(RNG.normal(12, 7), 1, 45))
        floor = int(RNG.integers(0, total_floors + 1))

    furnishing = RNG.choice(FURNISHING_STATUSES, p=[0.40, 0.38, 0.22])
    age_band, age_years, age_mult = sample_age()

    amenities_flags = {}
    for key, weight in AMENITIES.items():
        base_p = 0.35 + weight * 6  # pricier amenities slightly rarer/co-occur with newer builds
        amenities_flags[key] = int(RNG.random() < min(base_p, 0.75))

    amenity_bonus = sum(w for k, w in AMENITIES.items() if amenities_flags[k])

    per_sqft = (
        city["base_rate"]
        * loc_mult
        * TYPE_MULT[property_type]
        * FURNISH_MULT[furnishing]
        * age_mult
        * floor_mult(property_type, floor, total_floors)
        * config_mult(area, bhk, bathrooms)
        * (1 + amenity_bonus)
        * scale_mult(area)
    )
    noise = RNG.normal(1.0, 0.07)
    per_sqft = max(per_sqft * noise, 800)
    price = per_sqft * area

    row = {
        "city": city_id,
        "state": city["state"],
        "locality": locality,
        "area_sqft": round(area, 1),
        "bhk": bhk,
        "bathrooms": bathrooms,
        "floor": floor,
        "total_floors": total_floors,
        "property_age_years": age_years,
        "age_band": age_band,
        "furnishing_status": furnishing,
        "property_type": property_type,
        "price": round(price, -2),
        "price_per_sqft": round(per_sqft, 1),
    }
    for key in AMENITY_KEYS:
        row[key] = amenities_flags[key]
    return row


def inject_missing(df, cols, frac=0.03):
    for col in cols:
        idx = df.sample(frac=frac, random_state=RNG.integers(0, 1_000_000)).index
        df.loc[idx, col] = np.nan
    return df


def inject_outliers(df, frac=0.015):
    idx = df.sample(frac=frac, random_state=7).index
    factor = RNG.choice([0.25, 0.3, 3.2, 4.0], size=len(idx))
    df.loc[idx, "price"] = (df.loc[idx, "price"] * factor).round(-2)
    df.loc[idx, "price_per_sqft"] = (df.loc[idx, "price"] / df.loc[idx, "area_sqft"]).round(1)
    return df


def main():
    rows = [gen_row() for _ in range(N_ROWS)]
    df = pd.DataFrame(rows)

    df = inject_missing(df, ["bathrooms", "total_floors", "property_age_years"], frac=0.03)
    df = inject_outliers(df, frac=0.015)

    # small duplicate contamination, another thing real scraped data has
    dup_idx = df.sample(frac=0.005, random_state=11).index
    df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)

    df = df.sample(frac=1, random_state=1).reset_index(drop=True)
    df.insert(0, "listing_id", [f"L{100000+i}" for i in range(len(df))])

    out_path = "data/india_housing_raw.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")
    print(df.isna().sum()[df.isna().sum() > 0])


if __name__ == "__main__":
    main()
