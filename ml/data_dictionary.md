# Data Dictionary — `data/india_housing_raw.csv`

Synthetic dataset, 18,090 rows (incl. ~90 intentional duplicates), 12 Indian cities.
See `generate_dataset.py` for provenance — swap in a real dataset with matching
columns to replace this without touching the rest of the pipeline.

| Column | Type | Description | Valid range / values |
|---|---|---|---|
| `listing_id` | string | Synthetic unique ID | `L100000`–`L118089` |
| `city` | categorical | City slug | mumbai, delhi, bengaluru, pune, hyderabad, chennai, kolkata, ahmedabad, jaipur, chandigarh, lucknow, kochi |
| `state` | categorical | State/UT name | derived from `city` |
| `locality` | categorical | Neighbourhood within the city | 6 per city, see `city_data.py` |
| `area_sqft` | float | Carpet area | 250 – 8000 |
| `bhk` | int | Bedrooms | 1 – 5 |
| `bathrooms` | int (nullable) | Bathrooms | 1 – 6, **~3% missing** |
| `floor` | int | Floor number (0 = ground; 0 for plots) | 0 – 45 |
| `total_floors` | int (nullable) | Total floors in building (0 for plots) | 0 – 45, **~3% missing** |
| `property_age_years` | int (nullable) | Age in years | 0 – 39, **~3% missing** |
| `age_band` | categorical | Bucketed age | new, 1-5, 5-10, 10-20, 20+ |
| `furnishing_status` | categorical | Furnishing | unfurnished, semi, full |
| `property_type` | categorical | Listing type | apartment, villa, independent, plot |
| `parking`, `lift`, `security`, `power_backup`, `gym`, `pool`, `clubhouse`, `garden` | bool (0/1) | Amenity flags | 0 or 1 |
| `price` | float | **Target.** Total price (₹) | contains **~1.5% injected outliers** (data-entry-style errors) |
| `price_per_sqft` | float | `price / area_sqft` | derived, also has outliers |

## Known data quality issues (by design, for the pipeline to handle)
- Missing values in `bathrooms`, `total_floors`, `property_age_years` (~3% each)
- ~1.5% of rows have `price` corrupted by a 0.25×–4× factor (outliers)
- ~0.5% duplicate rows
