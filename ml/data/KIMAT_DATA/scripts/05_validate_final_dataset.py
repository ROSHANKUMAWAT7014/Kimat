import os
import pandas as pd
import numpy as np
import json
from pathlib import Path

BASE_DIR = Path("ml/data/KIMAT_DATA")
MERGED_FILE = BASE_DIR / "merged" / "kimat_property_merged.csv"
FINAL_DIR = BASE_DIR / "final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)
FINAL_FILE = FINAL_DIR / "kimat_pan_india_property_data.csv"

def validate_datasets():
    print("Starting validation phase...")
    try:
        df = pd.read_csv(MERGED_FILE, low_memory=False)
    except Exception as e:
        print(f"Error reading merged file: {e}")
        return
        
    df.to_csv(FINAL_FILE, index=False)
    
    total_rows, total_cols = df.shape
    
    # Unique counts
    states = df["state"].nunique(dropna=True) if "state" in df.columns else 0
    districts = df["district"].nunique(dropna=True) if "district" in df.columns else 0
    cities = df["city"].nunique(dropna=True) if "city" in df.columns else 0
    localities = df["locality"].nunique(dropna=True) if "locality" in df.columns else 0
    
    # Missing pct
    missing_pct = (df.isna().sum() / total_rows * 100).round(2).to_dict()
    
    # Dupes
    dupes = int(df.duplicated().sum())
    
    # Numeric stats
    min_price = float(df["total_price"].min()) if "total_price" in df.columns else None
    max_price = float(df["total_price"].max()) if "total_price" in df.columns else None
    med_price = float(df["total_price"].median()) if "total_price" in df.columns else None
    
    min_area = float(df["builtup_area_sqft"].min()) if "builtup_area_sqft" in df.columns else None
    max_area = float(df["builtup_area_sqft"].max()) if "builtup_area_sqft" in df.columns else None
    med_area = float(df["builtup_area_sqft"].median()) if "builtup_area_sqft" in df.columns else None

    # Group counts
    state_counts = df["state"].value_counts(dropna=False).to_dict() if "state" in df.columns else {}
    city_counts = df["city"].value_counts(dropna=False).to_dict() if "city" in df.columns else {}
    source_counts = df["source"].value_counts(dropna=False).to_dict() if "source" in df.columns else {}
    
    summary = {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "states": states,
        "districts": districts,
        "cities": cities,
        "localities": localities,
        "duplicate_counts": dupes,
        "min_price": min_price,
        "max_price": max_price,
        "median_price": med_price,
        "min_area": min_area,
        "max_area": max_area,
        "median_area": med_area
    }
    
    # Save simple summary CSV
    pd.DataFrame([summary]).to_csv(FINAL_DIR / "kimat_dataset_summary.csv", index=False)
    
    # Save missing
    pd.DataFrame(list(missing_pct.items()), columns=["Column", "Missing_Pct"]).to_csv(FINAL_DIR / "kimat_missing_summary.csv", index=False)
    
    # Save group counts
    pd.DataFrame(list(state_counts.items()), columns=["State", "Count"]).to_csv(FINAL_DIR / "kimat_state_counts.csv", index=False)
    pd.DataFrame(list(city_counts.items()), columns=["City", "Count"]).to_csv(FINAL_DIR / "kimat_city_counts.csv", index=False)
    pd.DataFrame(list(source_counts.items()), columns=["Source", "Count"]).to_csv(FINAL_DIR / "kimat_source_counts.csv", index=False)
    
    # Dump full JSON for the AI to read easily
    full_json = {
        "summary": summary,
        "missing_pct": missing_pct,
        "state_counts": state_counts,
        "city_counts": city_counts,
        "source_counts": source_counts
    }
    
    print("VALIDATION_JSON_START")
    print(json.dumps(full_json))
    print("VALIDATION_JSON_END")
    
    print("Validation complete. Final dataset and summaries saved.")

if __name__ == "__main__":
    validate_datasets()
