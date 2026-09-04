import os
import glob
import pandas as pd
import json
import numpy as np
from pathlib import Path
from pymongo import MongoClient

# Paths
BASE_DIR = Path("ml/data/KIMAT_DATA")
RAW_DIR = BASE_DIR / "raw"
INSPECTION_DIR = BASE_DIR / "inspection"
INSPECTION_DIR.mkdir(parents=True, exist_ok=True)

def inspect_datasets():
    print("Starting inspection phase...")
    files = []
    files.extend(glob.glob(str(RAW_DIR / "**/*.csv"), recursive=True))
    files.extend(glob.glob(str(RAW_DIR / "**/*.xlsx"), recursive=True))
    files.extend(glob.glob(str(RAW_DIR / "**/*.json"), recursive=True))

    inspection_data = []
    column_data = []
    coverage_data = []
    manual_review_rows = []

    KIMAT_SCHEMA = {
        "state", "district", "city", "locality", "pincode", "latitude", "longitude",
        "property_type", "bhk", "bathrooms", "balconies", "carpet_area_sqft", 
        "builtup_area_sqft", "superbuiltup_area_sqft", "floor", "total_floors", 
        "property_age", "furnished", "parking", "lift", "security", "gated_community", 
        "amenities_count", "construction_year", "property_status", "new_or_resale",
        "total_price", "price_per_sqft"
    }
    
    # Simple heuristic mappings (source_col -> target_col)
    MAPPING_HEURISTICS = {
        "price": "total_price",
        "amount": "total_price",
        "cost": "total_price",
        "bedrooms": "bhk",
        "bedroom": "bhk",
        "rooms": "bhk",
        "bath": "bathrooms",
        "baths": "bathrooms",
        "area": "builtup_area_sqft",
        "sqft": "builtup_area_sqft",
        "size": "builtup_area_sqft",
        "type": "property_type",
        "prop_type": "property_type",
        "neighborhood": "locality",
        "location": "locality",
        "region": "locality",
        "pin": "pincode",
        "zip": "pincode",
        "lat": "latitude",
        "lng": "longitude",
        "lon": "longitude",
        "furnishing": "furnished",
        "status": "property_status",
        "age": "property_age"
    }

    markdown_report = ["# KIMAT Data Analysis Report\n\n"]

    for f in files:
        file_path = Path(f)
        file_name = file_path.name
        print(f"Inspecting {file_name}...")
        
        try:
            if file_name.endswith(".csv"):
                df = pd.read_csv(f)
            elif file_name.endswith(".xlsx"):
                df = pd.read_excel(f)
            elif file_name.endswith(".json"):
                df = pd.read_json(f)
        except Exception as e:
            print(f"Error reading {file_name}: {e}")
            continue

        num_rows, num_cols = df.shape
        markdown_report.append(f"## Dataset: {file_name}\n")
        markdown_report.append(f"- **Rows**: {num_rows}\n")
        markdown_report.append(f"- **Columns**: {num_cols}\n\n")

        # Column stats
        for col in df.columns:
            dtype = str(df[col].dtype)
            missing_pct = (df[col].isna().sum() / num_rows) * 100 if num_rows > 0 else 0
            
            unique_vals = 0
            min_val, max_val, median_val = None, None, None
            
            if pd.api.types.is_numeric_dtype(df[col]):
                min_val = df[col].min()
                max_val = df[col].max()
                median_val = df[col].median()
            else:
                try:
                    unique_vals = df[col].nunique()
                except TypeError:
                    unique_vals = df[col].astype(str).nunique()
            
            column_data.append({
                "dataset": file_name,
                "column": col,
                "dtype": dtype,
                "missing_pct": float(round(missing_pct, 2)),
                "unique_vals": int(unique_vals) if pd.notna(unique_vals) else 0,
                "min": float(min_val) if pd.notna(min_val) else None,
                "max": float(max_val) if pd.notna(max_val) else None,
                "median": float(median_val) if pd.notna(median_val) else None
            })
            
            # Auto-mapping
            col_lower = str(col).lower().strip()
            mapped = False
            target_col = None
            if col_lower in KIMAT_SCHEMA:
                target_col = col_lower
                mapped = True
            else:
                for key, val in MAPPING_HEURISTICS.items():
                    if key in col_lower:
                        target_col = val
                        mapped = True
                        break
            
            if mapped:
                manual_review_rows.append({"dataset": file_name, "source_column": col, "proposed_mapping": target_col, "status": "heuristic_mapped"})
            else:
                manual_review_rows.append({"dataset": file_name, "source_column": col, "proposed_mapping": "UNKNOWN", "status": "needs_review"})

        # Check coverage of key concepts
        col_names = [str(c).lower() for c in df.columns]
        
        has_state = any("state" in c for c in col_names)
        has_city = any("city" in c for c in col_names)
        has_district = any("district" in c for c in col_names)
        has_locality = any(c in ["locality", "neighborhood", "location", "address"] for c in col_names)
        has_price = any(c in ["price", "cost", "amount"] for c in col_names)
        has_area = any(c in ["area", "sqft", "size"] for c in col_names)
        has_dupes = df.duplicated().any() if num_rows > 0 else False
        has_latlong = any("lat" in c for c in col_names) and any("lon" in c or "lng" in c for c in col_names)
        has_bhk = any(c in ["bhk", "bedroom", "bedrooms", "rooms"] for c in col_names)
        has_bath = any(c in ["bath", "bathrooms", "baths"] for c in col_names)
        has_type = any(c in ["type", "property_type"] for c in col_names)
        has_age = any(c in ["age", "year", "construction"] for c in col_names)
        has_amenities = any(c in ["amenities", "facilities"] for c in col_names)
        has_parking = any("parking" in c for c in col_names)
        has_date = any("date" in c for c in col_names)

        inspection_data.append({
            "dataset": file_name,
            "rows": int(num_rows),
            "columns": int(num_cols),
            "has_state": bool(has_state),
            "has_city": bool(has_city),
            "has_district": bool(has_district),
            "has_locality": bool(has_locality),
            "has_price": bool(has_price),
            "has_area": bool(has_area),
            "has_duplicates": bool(has_dupes),
            "has_latlong": bool(has_latlong),
            "has_bhk": bool(has_bhk),
            "has_bath": bool(has_bath),
            "has_type": bool(has_type),
            "has_age": bool(has_age),
            "has_amenities": bool(has_amenities),
            "has_parking_lift_sec": bool(has_parking),
            "has_date": bool(has_date)
        })

    # Save to CSV
    pd.DataFrame(inspection_data).to_csv(INSPECTION_DIR / "dataset_inspection_report.csv", index=False)
    pd.DataFrame(column_data).to_csv(INSPECTION_DIR / "dataset_column_report.csv", index=False)
    pd.DataFrame(manual_review_rows).to_csv(INSPECTION_DIR / "manual_review_required.csv", index=False)
    
    # Save markdown
    with open(INSPECTION_DIR / "DATA_ANALYSIS_REPORT.md", "w") as f:
        f.writelines(markdown_report)

    # MongoDB Integration
    try:
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Verify connection
        client.server_info()
        
        db = client["kimat_data_pipeline"]
        
        # Access collections
        col_inspection = db["inspection_reports"]
        col_columns = db["column_reports"]
        col_reviews = db["manual_reviews"]
        
        # Clear old inspection data so it doesn't infinitely append
        col_inspection.delete_many({})
        col_columns.delete_many({})
        col_reviews.delete_many({})
        
        # Insert new data
        if inspection_data:
            col_inspection.insert_many(inspection_data)
        if column_data:
            col_columns.insert_many(column_data)
        if manual_review_rows:
            col_reviews.insert_many(manual_review_rows)
            
        print(f"MongoDB: Successfully logged inspection reports to {mongo_uri} (db: kimat_data_pipeline)")
    except Exception as e:
        print(f"MongoDB connection failed. Reports are only saved locally as CSVs. Error: {e}")

    print(f"Inspection complete. Reports saved to {INSPECTION_DIR}")

if __name__ == "__main__":
    inspect_datasets()
