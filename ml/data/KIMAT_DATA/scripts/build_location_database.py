import pandas as pd
import glob
import json
import os
import re

RAW_DIR = 'ml/data/KIMAT_DATA/raw'
FINAL_DIR = 'ml/data/KIMAT_DATA/final'

os.makedirs(FINAL_DIR, exist_ok=True)

locations = []
normalizations = []

def normalize_text(text, field_name, source_file):
    if pd.isna(text) or text == '' or text == 'nan':
        return None
    original = str(text).strip()
    norm = original.title()
    
    mapping = {
        "Bangalore": "Bengaluru",
        "Bombay": "Mumbai",
        "Calcutta": "Kolkata",
        "Madras": "Chennai",
        "New Delhi": "Delhi",
        "Ncr": "NCR"
    }
    
    for k, v in mapping.items():
        if k in norm:
            norm = norm.replace(k, v)
            
    if original != norm:
        normalizations.append({
            'original_value': original,
            'standardized_value': norm,
            'field': field_name,
            'source': source_file,
            'reason': 'Capitalization/Known alias'
        })
        
    return norm if norm else None

def add_loc(state, district, city, locality, pincode, source):
    st = normalize_text(state, 'state', source)
    dt = normalize_text(district, 'district', source)
    ct = normalize_text(city, 'city', source)
    loc = normalize_text(locality, 'locality', source)
    
    # Simple state inference for known major cities
    known_states = {
        'Mumbai': 'Maharashtra', 'Pune': 'Maharashtra', 'Nagpur': 'Maharashtra', 'Thane': 'Maharashtra',
        'Bengaluru': 'Karnataka', 'Mysore': 'Karnataka',
        'Delhi': 'Delhi', 'Delhi Ncr': 'Delhi', 'New Delhi': 'Delhi',
        'Chennai': 'Tamil Nadu', 'Coimbatore': 'Tamil Nadu',
        'Kolkata': 'West Bengal',
        'Ahmedabad': 'Gujarat', 'Surat': 'Gujarat', 'Vadodara': 'Gujarat',
        'Jaipur': 'Rajasthan',
        'Chandigarh': 'Chandigarh',
        'Lucknow': 'Uttar Pradesh', 'Ghaziabad': 'Uttar Pradesh', 'Noida': 'Uttar Pradesh',
        'Kochi': 'Kerala', 'Ernakulam': 'Kerala'
    }
    
    # Apply inference if state is missing
    if not st and ct in known_states:
        st = known_states[ct]
        
    st = st or 'Unknown State'
    dt = dt or ct or 'Unknown District'
    ct = ct or dt or 'Unknown City'
    loc = loc or ct or 'Unknown Locality'
    pin = str(pincode).replace(".0", "").strip() if pd.notna(pincode) else ""
    if pin == 'nan': pin = ""
    
    locations.append({
        'state': st,
        'district': dt,
        'city': ct,
        'locality': loc,
        'pincode': pin,
        'source': source
    })

print("Processing Dataset 1...")
for file in glob.glob(f'{RAW_DIR}/dataset_1_statewise/*.csv'):
    try:
        df = pd.read_csv(file, on_bad_lines='skip', engine='python')
        source = f"dataset_1/{os.path.basename(file)}"
        for _, row in df.iterrows():
            st = row.get('state')
            ct = row.get('city')
            add_loc(st, ct, ct, ct, None, source)
    except Exception as e:
        print(f"Skipping {file}: {e}")

print("Processing Dataset 2...")
for file in glob.glob(f'{RAW_DIR}/dataset_2_listings_2025/*.csv'):
    try:
        df = pd.read_csv(file, on_bad_lines='skip', engine='python')
        source = f"dataset_2/{os.path.basename(file)}"
        for _, row in df.iterrows():
            ct = row.get('city')
            loc = row.get('neighborhood')
            add_loc(None, ct, ct, loc, None, source)
    except Exception as e:
        print(f"Skipping {file}: {e}")

print("Processing Dataset 3...")
for file in glob.glob(f'{RAW_DIR}/dataset_3_real_estate/*.xlsx'):
    try:
        df = pd.read_excel(file)
        source = f"dataset_3/{os.path.basename(file)}"
        
        state_col = next((c for c in df.columns if 'state' in c.lower()), None)
        city_col = next((c for c in df.columns if 'city' in c.lower()), None)
        loc_col = next((c for c in df.columns if 'local' in c.lower() or 'area' in c.lower() or 'suburb' in c.lower()), None)
        
        for _, row in df.iterrows():
            st = row[state_col] if state_col else None
            ct = row[city_col] if city_col else None
            loc = row[loc_col] if loc_col else None
            add_loc(st, ct, ct, loc, None, source)
    except Exception as e:
        print(f"Skipping {file}: {e}")

print("Processing Dataset 4...")
for file in glob.glob(f'{RAW_DIR}/dataset_4_indian_cities/*.csv'):
    try:
        df = pd.read_csv(file, on_bad_lines='skip', engine='python')
        source = f"dataset_4/{os.path.basename(file)}"
        match = re.search(r'output_([A-Za-z0-9_]+)_', os.path.basename(file))
        ct = match.group(1).replace('_', ' ') if match else None
        
        for _, row in df.iterrows():
            loc = row.get('location')
            add_loc(None, ct, ct, loc, None, source)
    except Exception as e:
        print(f"Skipping {file}: {e}")

print("Building data structures...")
df_locs = pd.DataFrame(locations).drop_duplicates(subset=['state', 'district', 'city', 'locality', 'pincode'])

# Build JSON hierarchy
hierarchy = {}
for _, row in df_locs.iterrows():
    st = row['state']
    dt = row['district']
    ct = row['city']
    loc = row['locality']
    
    if st not in hierarchy: hierarchy[st] = {}
    if dt not in hierarchy[st]: hierarchy[st][dt] = {}
    if ct not in hierarchy[st][dt]: hierarchy[st][dt][ct] = set()
    hierarchy[st][dt][ct].add(loc)

# Convert sets to sorted lists
for st in hierarchy:
    for dt in hierarchy[st]:
        for ct in hierarchy[st][dt]:
            hierarchy[st][dt][ct] = sorted(list(hierarchy[st][dt][ct]))

# Write JSON
print("Writing JSON...")
json_path = f"{FINAL_DIR}/india_locations.json"
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(hierarchy, f, indent=2)

# Write Normalization Mapping
pd.DataFrame(normalizations).drop_duplicates().to_csv(f"{FINAL_DIR}/location_normalization_mapping.csv", index=False)

# Coverage Report
total_states = len(df_locs['state'].unique())
total_districts = len(df_locs['district'].unique())
total_cities = len(df_locs['city'].unique())
total_localities = len(df_locs['locality'].unique())
total_pincodes = len(df_locs[df_locs['pincode'] != '']['pincode'].unique())
total_records = len(df_locs)

state_counts = df_locs.groupby('state').agg(
    districts=('district', 'nunique'),
    cities=('city', 'nunique'),
    localities=('locality', 'nunique')
).reset_index().sort_values('localities', ascending=False)
state_counts.to_csv(f"{FINAL_DIR}/location_coverage_report.csv", index=False)

md_content = f"""# KIMAT Location Coverage Report

## Overall Statistics
- **Total Unique States**: {total_states}
- **Total Unique Districts**: {total_districts}
- **Total Unique Cities/Towns**: {total_cities}
- **Total Unique Areas/Localities**: {total_localities}
- **Total Unique Pincodes**: {total_pincodes}
- **Total Mapped Records**: {total_records}

## Coverage by State
| State | Districts | Cities | Localities |
|-------|-----------|--------|------------|
"""
for _, row in state_counts.iterrows():
    md_content += f"| {row['state']} | {row['districts']} | {row['cities']} | {row['localities']} |\n"

with open(f"{FINAL_DIR}/location_coverage_report.md", 'w', encoding='utf-8') as f:
    f.write(md_content)

print("Done! Artifacts generated in ml/data/KIMAT_DATA/final/")
