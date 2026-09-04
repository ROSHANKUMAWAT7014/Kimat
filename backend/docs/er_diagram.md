# ER Diagram — Kimat Database

```mermaid
erDiagram
    LISTINGS {
        int id PK
        string listing_id UK
        string city
        string state
        string locality
        float area_sqft
        int bhk
        int bathrooms
        int floor
        int total_floors
        int property_age_years
        string age_band
        string furnishing_status
        string property_type
        bool parking
        bool lift
        bool security
        bool power_backup
        bool gym
        bool pool
        bool clubhouse
        bool garden
        float price
        float price_per_sqft
    }

    PREDICTION_LOGS {
        int id PK
        datetime created_at
        string city
        string locality
        float area_sqft
        int bhk
        int bathrooms
        int floor
        int total_floors
        int property_age_years
        string furnishing_status
        string property_type
        string amenities_csv
        float predicted_price
        float price_low
        float price_high
        string model_used
        string client_ip
    }

    CITY_STATS_CACHE {
        string city PK
        string state
        float avg_price_per_sqft
        float yoy_growth_pct
        int locality_count
        int listing_count
        datetime updated_at
    }
```

## Notes

- **`listings`** — training/reference data, seeded from `ml/data/india_housing_raw.csv`
  via `seed_db.py` after `preprocessing.clean()` runs. Not written to at request time.
- **`prediction_logs`** — one row per `POST /predict` call, written by a
  `BackgroundTask` *after* the response is already sent (non-blocking).
- **`city_stats_cache`** — one row per city, refreshed by `seed_db.py`.
  `GET /city-stats` reads this instead of aggregating `listings` live on
  every request.
- No foreign keys between the three tables by design — they're independent
  facts (reference data, an audit log, a cache), not a normalized
  transactional schema.
- **Not yet implemented** (optional per the spec, "if login is added"): a
  `users` table and a `bookmarks` table (`user_id` FK → `users.id`,
  `locality` or `listing_id` reference). Add these only if/when auth ships —
  no other table needs to change to support it.
