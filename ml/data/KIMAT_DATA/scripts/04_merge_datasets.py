import os
import glob
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("ml/data/KIMAT_DATA")
CLEANED_DIR = BASE_DIR / "cleaned"
MERGED_DIR = BASE_DIR / "merged"
MERGED_DIR.mkdir(parents=True, exist_ok=True)

KIMAT_SCHEMA = [
    "source", "state", "district", "city", "locality", "pincode", "latitude", "longitude",
    "property_type", "bhk", "bathrooms", "balconies", "carpet_area_sqft", 
    "builtup_area_sqft", "superbuiltup_area_sqft", "floor", "total_floors", 
    "property_age", "furnished", "parking", "lift", "security", "gated_community", 
    "amenities_count", "construction_year", "property_status", "new_or_resale",
    "distance_to_city_center", "distance_to_metro", "distance_to_railway", "distance_to_airport", 
    "distance_to_school", "distance_to_hospital", "circle_rate", "guidance_value", 
    "population", "population_density", "literacy_rate",
    "total_price", "price_per_sqft", "transaction_date", "listing_id", "data_type"
]

GOV_DEMOGRAPHIC_COLS = [
    "circle_rate", "guidance_value", "population", "population_density", "literacy_rate",
    "distance_to_city_center", "distance_to_metro", "distance_to_railway", 
    "distance_to_airport", "distance_to_school", "distance_to_hospital"
]

def merge_datasets():
    print("Starting merging phase...")
    files = glob.glob(str(CLEANED_DIR / "*_cleaned.csv"))
    
    dfs = []
    
    for f in files:
        file_path = Path(f)
        file_name = file_path.name
        print(f"Loading {file_name}...")
        
        try:
            df = pd.read_csv(f, low_memory=False)
        except Exception as e:
            print(f"Error reading {file_name}: {e}")
            continue

        # Extract source prefix
        # We named them parent_dir_filename_cleaned.csv
        # Let's just use the file_name as source or extract dataset_X_name
        source_name = file_name.replace("_cleaned.csv", "")
        df["source"] = source_name
        
        # Calculate price_per_sqft
        if "total_price" in df.columns and "builtup_area_sqft" in df.columns:
            # Only where both > 0
            valid_mask = (df["total_price"] > 0) & (df["builtup_area_sqft"] > 0)
            df.loc[valid_mask, "price_per_sqft"] = df.loc[valid_mask, "total_price"] / df.loc[valid_mask, "builtup_area_sqft"]
        else:
            if "price_per_sqft" not in df.columns:
                df["price_per_sqft"] = np.nan
        
        dfs.append(df)
        
    if not dfs:
        print("No datasets to merge!")
        return

    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Phase 8: Do not fabricate government data. Enforce strictly NaN.
    for gov_col in GOV_DEMOGRAPHIC_COLS:
        merged_df[gov_col] = np.nan
        
    # Ensure all KIMAT schema columns exist
    for col in KIMAT_SCHEMA:
        if col not in merged_df.columns:
            merged_df[col] = np.nan
            
    # Filter only schema columns just to be clean, or keep all?
    # Instruction: "Use a consistent unified schema."
    # We will keep only schema columns + any extra ones that mapped to them.
    # We will reorder to KIMAT_SCHEMA, dropping unmapped columns.
    merged_df = merged_df[KIMAT_SCHEMA]
    
    out_file = MERGED_DIR / "kimat_property_merged.csv"
    merged_df.to_csv(out_file, index=False)
    
    print(f"Merge complete. Output saved to {out_file} with shape {merged_df.shape}")

if __name__ == "__main__":
    merge_datasets()
