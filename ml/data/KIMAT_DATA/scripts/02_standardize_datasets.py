import os
import glob
import pandas as pd
import numpy as np
import re
from pathlib import Path

BASE_DIR = Path("ml/data/KIMAT_DATA")
RAW_DIR = BASE_DIR / "raw"
CLEANED_DIR = BASE_DIR / "cleaned"
CLEANED_DIR.mkdir(parents=True, exist_ok=True)

MAPPING_HEURISTICS = {
    "price": "total_price", "amount": "total_price", "cost": "total_price",
    "bedrooms": "bhk", "bedroom": "bhk", "rooms": "bhk", "bhk": "bhk",
    "bath": "bathrooms", "bathrooms": "bathrooms", "baths": "bathrooms",
    "area": "builtup_area_sqft", "sqft": "builtup_area_sqft", "size": "builtup_area_sqft",
    "type": "property_type", "prop_type": "property_type",
    "neighborhood": "locality", "location": "locality", "region": "locality", "locality": "locality",
    "pin": "pincode", "zip": "pincode", "pincode": "pincode",
    "lat": "latitude", "latitude": "latitude", "lng": "longitude", "lon": "longitude", "longitude": "longitude",
    "furnishing": "furnished", "furnished": "furnished",
    "status": "property_status", "property_status": "property_status",
    "age": "property_age", "property_age": "property_age",
    "state": "state", "district": "district", "city": "city"
}

def clean_price(val):
    if pd.isna(val): return np.nan
    val_str = str(val).lower().replace(",", "").replace("rs.", "").replace("inr", "").replace("₹", "").strip()
    try:
        if "cr" in val_str or "crore" in val_str:
            num = float(re.findall(r"[\d\.]+", val_str)[0])
            return num * 10000000
        elif "lakh" in val_str or "lac" in val_str:
            num = float(re.findall(r"[\d\.]+", val_str)[0])
            return num * 100000
        elif "k" in val_str:
            num = float(re.findall(r"[\d\.]+", val_str)[0])
            return num * 1000
        else:
            nums = re.findall(r"[\d\.]+", val_str)
            if nums: return float(nums[0])
            return np.nan
    except:
        return np.nan

def clean_area(val):
    if pd.isna(val): return np.nan
    val_str = str(val).lower().replace(",", "").strip()
    try:
        nums = re.findall(r"[\d\.]+", val_str)
        if not nums: return np.nan
        num = float(nums[0])
        if "sqm" in val_str or "sq.m" in val_str or "square meter" in val_str: return num * 10.764
        elif "sqyd" in val_str or "sq.yd" in val_str or "square yard" in val_str: return num * 9.0
        elif "acre" in val_str: return num * 43560.0
        elif "hectare" in val_str: return num * 107639.0
        elif "guntha" in val_str: return num * 1089.0
        elif "bigha" in val_str: return num * 27000.0 # Approx, varies heavily
        return num # assume sqft
    except:
        return np.nan

def clean_bhk(val):
    if pd.isna(val): return np.nan
    val_str = str(val).lower()
    try:
        nums = re.findall(r"[\d\.]+", val_str)
        if nums: return float(nums[0])
        return np.nan
    except:
        return np.nan

def standardize_boolean(val):
    if pd.isna(val): return np.nan
    val_str = str(val).strip().lower()
    if val_str in ["yes", "y", "true", "1", "1.0", "t"]: return True
    if val_str in ["no", "n", "false", "0", "0.0", "f"]: return False
    return np.nan

def standardize_furnishing(val):
    if pd.isna(val): return np.nan
    val_str = str(val).lower()
    if "semi" in val_str: return "Semi Furnished"
    if "un" in val_str or "not" in val_str or "no" in val_str: return "Unfurnished"
    if "full" in val_str or "furnished" in val_str: return "Fully Furnished"
    return val

def standardize_property_type(val):
    if pd.isna(val): return np.nan
    val_str = str(val).lower()
    if "flat" in val_str or "apartment" in val_str: return "Apartment"
    if "villa" in val_str or "house" in val_str or "independent" in val_str: return "Villa/Independent House"
    if "plot" in val_str or "land" in val_str: return "Plot/Land"
    if "builder" in val_str or "floor" in val_str: return "Builder Floor"
    if "commercial" in val_str or "office" in val_str or "shop" in val_str: return "Commercial"
    return str(val).title()

def standardize_datasets():
    print("Starting standardization phase...")
    files = []
    files.extend(glob.glob(str(RAW_DIR / "**/*.csv"), recursive=True))
    files.extend(glob.glob(str(RAW_DIR / "**/*.xlsx"), recursive=True))
    files.extend(glob.glob(str(RAW_DIR / "**/*.json"), recursive=True))
    
    location_mappings = []

    for idx, f in enumerate(files):
        file_path = Path(f)
        parent_dir = file_path.parent.name
        print(f"Standardizing {file_path.name} from {parent_dir}...")
        
        try:
            if file_path.suffix == ".csv": df = pd.read_csv(f)
            elif file_path.suffix == ".xlsx": df = pd.read_excel(f)
            elif file_path.suffix == ".json": df = pd.read_json(f)
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
            continue
            
        # Map columns
        new_cols = {}
        mapped_targets = set()
        for col in df.columns:
            c_lower = str(col).lower().strip()
            mapped = False
            for k, v in MAPPING_HEURISTICS.items():
                if k in c_lower:
                    if v not in mapped_targets:
                        new_cols[col] = v
                        mapped_targets.add(v)
                        mapped = True
                    break
            if not mapped:
                new_col_fallback = str(col).lower().replace(" ", "_")
                if new_col_fallback not in mapped_targets:
                    new_cols[col] = new_col_fallback
                    mapped_targets.add(new_col_fallback)
        df.rename(columns=new_cols, inplace=True)
        # Drop any remaining duplicated columns
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Clean specific columns if they exist
        if "total_price" in df.columns:
            df["total_price"] = df["total_price"].apply(clean_price)
        if "builtup_area_sqft" in df.columns:
            df["builtup_area_sqft"] = df["builtup_area_sqft"].apply(clean_area)
        if "bhk" in df.columns:
            df["bhk"] = df["bhk"].apply(clean_bhk)
        if "furnished" in df.columns:
            df["furnished"] = df["furnished"].apply(standardize_furnishing)
        if "property_type" in df.columns:
            df["property_type"] = df["property_type"].apply(standardize_property_type)
            
        # Standardize booleans
        bool_cols = ["parking", "lift", "security", "gated_community", "new_or_resale"]
        for bc in bool_cols:
            if bc in df.columns:
                df[bc] = df[bc].apply(standardize_boolean)
                
        # Location Standardization
        loc_cols = ["city", "district", "state"]
        for lc in loc_cols:
            if lc in df.columns:
                df[lc] = df[lc].astype(str).replace("nan", np.nan)
                unique_locs = df[lc].dropna().unique()
                for loc in unique_locs:
                    original = str(loc)
                    standardized = original.strip().title()
                    # Apply specific normalizations
                    if standardized == "Bangalore": standardized = "Bengaluru"
                    elif standardized == "Bombay": standardized = "Mumbai"
                    elif standardized == "Madras": standardized = "Chennai"
                    elif standardized == "Calcutta": standardized = "Kolkata"
                    elif standardized == "Trivandrum": standardized = "Thiruvananthapuram"
                    elif standardized == "Pondicherry": standardized = "Puducherry"
                    elif standardized == "Gurgaon": standardized = "Gurugram"
                    elif standardized == "Mangalore": standardized = "Mangaluru"
                    elif standardized == "Baroda": standardized = "Vadodara"
                    elif standardized == "Poona": standardized = "Pune"
                    elif standardized == "Cochin": standardized = "Kochi"
                    
                    if original != standardized:
                        location_mappings.append({
                            "original_value": original,
                            "standardized_value": standardized,
                            "field": lc,
                            "reason": "Normalized spelling/case"
                        })
                
                # Apply map
                def apply_loc_map(val):
                    if pd.isna(val): return val
                    val_str = str(val).strip().title()
                    map_dict = {"Bangalore": "Bengaluru", "Bombay": "Mumbai", "Madras": "Chennai", 
                                "Calcutta": "Kolkata", "Trivandrum": "Thiruvananthapuram", 
                                "Pondicherry": "Puducherry", "Gurgaon": "Gurugram", 
                                "Mangalore": "Mangaluru", "Baroda": "Vadodara", "Poona": "Pune", "Cochin": "Kochi"}
                    return map_dict.get(val_str, val_str)
                
                df[lc] = df[lc].apply(apply_loc_map)
                
        # Save cleaned dataset
        out_name = f"{parent_dir}_{file_path.stem}_cleaned.csv"
        df.to_csv(CLEANED_DIR / out_name, index=False)

    pd.DataFrame(location_mappings).drop_duplicates().to_csv(CLEANED_DIR / "location_normalization_mapping.csv", index=False)
    print("Standardization complete.")

if __name__ == "__main__":
    standardize_datasets()
