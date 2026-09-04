import os
import glob
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("ml/data/KIMAT_DATA")
CLEANED_DIR = BASE_DIR / "cleaned"

def clean_datasets():
    print("Starting cleaning phase...")
    files = glob.glob(str(CLEANED_DIR / "*_cleaned.csv"))
    
    quality_flags = []
    duplicate_reviews = []
    
    for f in files:
        file_path = Path(f)
        file_name = file_path.name
        print(f"Cleaning {file_name}...")
        
        try:
            df = pd.read_csv(f)
        except Exception as e:
            print(f"Error reading {file_name}: {e}")
            continue

        original_count = len(df)
        if original_count == 0: continue
            
        # 1. Duplicate Detection
        exact_dupes_mask = df.duplicated(keep='first')
        exact_dupes = df[exact_dupes_mask].copy()
        if not exact_dupes.empty:
            exact_dupes['duplicate_type'] = 'exact_duplicate'
            exact_dupes['dataset'] = file_name
            duplicate_reviews.append(exact_dupes)
            
        # Remove exact duplicates
        df = df[~exact_dupes_mask]
        
        # Probable duplicates (heuristic: same location, type, bhk, area, price)
        prob_cols = []
        for c in ["state", "city", "locality", "property_type", "bhk", "builtup_area_sqft", "total_price"]:
            if c in df.columns:
                prob_cols.append(c)
                
        if len(prob_cols) > 4:
            # We need enough columns to confidently say it's a probable duplicate
            prob_dupes_mask = df.duplicated(subset=prob_cols, keep=False)
            # Only keep the 'duplicate' ones, excluding the first occurrence to not remove everything
            prob_dupes = df[prob_dupes_mask].copy()
            if not prob_dupes.empty:
                # We don't remove probable duplicates as per instruction, just log them
                prob_dupes_log = df[df.duplicated(subset=prob_cols, keep='first')].copy()
                prob_dupes_log['duplicate_type'] = 'probable_duplicate'
                prob_dupes_log['dataset'] = file_name
                duplicate_reviews.append(prob_dupes_log)

        # 2. Data Quality
        to_drop = pd.Series(False, index=df.index)
        
        if "total_price" in df.columns:
            invalid_price = (df["total_price"] <= 0) | (df["total_price"].isna() == False) & (df["total_price"] > 1e12) # 1 trillion INR is unrealistic
            flag_df = df[invalid_price].copy()
            if not flag_df.empty:
                flag_df['flag_reason'] = 'Invalid total_price'
                flag_df['dataset'] = file_name
                quality_flags.append(flag_df)
                to_drop = to_drop | (df["total_price"] <= 0)
                
        if "builtup_area_sqft" in df.columns:
            invalid_area = (df["builtup_area_sqft"] <= 0)
            flag_df = df[invalid_area].copy()
            if not flag_df.empty:
                flag_df['flag_reason'] = 'Invalid builtup_area_sqft'
                flag_df['dataset'] = file_name
                quality_flags.append(flag_df)
                to_drop = to_drop | invalid_area
                
        if "bhk" in df.columns:
            invalid_bhk = (df["bhk"] <= 0)
            flag_df = df[invalid_bhk].copy()
            if not flag_df.empty:
                flag_df['flag_reason'] = 'Invalid bhk'
                flag_df['dataset'] = file_name
                quality_flags.append(flag_df)
                to_drop = to_drop | invalid_bhk
                
        if "bathrooms" in df.columns:
            invalid_bath = (df["bathrooms"] < 0)
            flag_df = df[invalid_bath].copy()
            if not flag_df.empty:
                flag_df['flag_reason'] = 'Negative bathrooms'
                flag_df['dataset'] = file_name
                quality_flags.append(flag_df)
                to_drop = to_drop | invalid_bath
                
        if "latitude" in df.columns and "longitude" in df.columns:
            invalid_coords = (df["latitude"] < -90) | (df["latitude"] > 90) | (df["longitude"] < -180) | (df["longitude"] > 180)
            flag_df = df[invalid_coords].copy()
            if not flag_df.empty:
                flag_df['flag_reason'] = 'Invalid coordinates'
                flag_df['dataset'] = file_name
                quality_flags.append(flag_df)
                to_drop = to_drop | invalid_coords
                
        # Remove only clearly invalid records
        df = df[~to_drop]
        
        # Save back to cleaned folder, overwriting with strictly filtered version
        df.to_csv(file_path, index=False)
        print(f"  Removed {to_drop.sum()} invalid and {exact_dupes_mask.sum()} exact dupes.")

    if quality_flags:
        pd.concat(quality_flags, ignore_index=True).to_csv(CLEANED_DIR / "data_quality_flags.csv", index=False)
    else:
        pd.DataFrame(columns=['dataset', 'flag_reason']).to_csv(CLEANED_DIR / "data_quality_flags.csv", index=False)
        
    if duplicate_reviews:
        pd.concat(duplicate_reviews, ignore_index=True).to_csv(CLEANED_DIR / "duplicate_review.csv", index=False)
    else:
        pd.DataFrame(columns=['dataset', 'duplicate_type']).to_csv(CLEANED_DIR / "duplicate_review.csv", index=False)

    print("Cleaning complete.")

if __name__ == "__main__":
    clean_datasets()
