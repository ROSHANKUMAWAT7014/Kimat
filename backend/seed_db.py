"""
Seed the database from ml/data/india_housing_raw.csv (cleaned via the same
preprocessing.clean() the training pipeline uses), and refresh the
city_stats_cache table GET /city-stats reads from.

Run once after training, and again whenever the dataset changes:
    python seed_db.py
"""

import ml_path
from city_data import CITIES
from preprocessing import clean
import pandas as pd

from database import get_listings_collection, get_stats_collection, MONGODB_URI

AMENITY_COLS = ["parking", "lift", "security", "power_backup", "gym", "pool", "clubhouse", "garden"]


def main():
    raw_path = ml_path.ML_DIR / "data" / "india_housing_raw.csv"
    try:
        df = clean(pd.read_csv(raw_path))
        print(f"Loaded {len(df)} cleaned rows from {raw_path}")
    except Exception as e:
        print(f"Error loading {raw_path}: {e}")
        return

    listings_col = get_listings_collection()
    stats_col = get_stats_collection()

    listings_col.delete_many({})
    stats_col.delete_many({})

    objects = [
        {
            "listing_id": row.listing_id, "city": row.city, "state": row.state, "locality": row.locality,
            "area_sqft": row.area_sqft, "bhk": row.bhk, "bathrooms": int(row.bathrooms), "floor": row.floor,
            "total_floors": int(row.total_floors), "property_age_years": int(row.property_age_years),
            "age_band": row.age_band, "furnishing_status": row.furnishing_status, "property_type": row.property_type,
            "parking": bool(row.parking), "lift": bool(row.lift), "security": bool(row.security),
            "power_backup": bool(row.power_backup), "gym": bool(row.gym), "pool": bool(row.pool),
            "clubhouse": bool(row.clubhouse), "garden": bool(row.garden),
            "price": row.price, "price_per_sqft": row.price_per_sqft,
        }
        for row in df.itertuples()
    ]
    
    if objects:
        listings_col.insert_many(objects)

    stats = df.groupby("city").agg(
        avg_price_per_sqft=("price_per_sqft", "mean"),
        locality_count=("locality", "nunique"),
        listing_count=("listing_id", "count"),
    )
    
    stats_docs = []
    for city_id, row in stats.iterrows():
        city_meta = CITIES.get(city_id, {})
        stats_docs.append({
            "city": city_id,
            "state": city_meta.get("state", ""),
            "avg_price_per_sqft": round(float(row["avg_price_per_sqft"]), 1),
            "yoy_growth_pct": round(city_meta.get("yoy", 0) * 100, 2),
            "locality_count": int(row["locality_count"]),
            "listing_count": int(row["listing_count"]),
        })
        
    if stats_docs:
        stats_col.insert_many(stats_docs)

    print(f"Seeded {len(objects)} listings and {len(stats_docs)} city_stats_cache rows into MongoDB at {MONGODB_URI}")


if __name__ == "__main__":
    main()
