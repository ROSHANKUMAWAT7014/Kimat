import pandas as pd
import json

df = pd.read_csv('ml/data/KIMAT_DATA/final/kimat_pan_india_property_data.csv', usecols=['state', 'district', 'city', 'locality'], on_bad_lines='skip', engine='python')
df = df.dropna()

locations = {}
for _, row in df.iterrows():
    state = str(row['state']).strip().title()
    district = str(row['district']).strip().title()
    city = str(row['city']).strip().title()
    locality = str(row['locality']).strip().title()
    
    if not state or not district or not city or not locality:
        continue
        
    if state not in locations:
        locations[state] = {}
    if district not in locations[state]:
        locations[state][district] = {}
    if city not in locations[state][district]:
        locations[state][district][city] = set()
        
    locations[state][district][city].add(locality)

# Convert sets to sorted lists
for state in locations:
    for district in locations[state]:
        for city in locations[state][district]:
            locations[state][district][city] = sorted(list(locations[state][district][city]))

ts_content = f"""/**
 * Normalized location database for Pan-India support.
 */
export const INDIA_LOCATIONS = {json.dumps(locations, indent=2)} as const;

/**
 * Maps the exact standardized string combination back to the internal `cityId`
 * required by the backend API and local ML coefficients.
 */
export const LOCATION_TO_CITY_ID: Record<string, string> = {{
  "Mumbai": "mumbai",
  "Delhi Ncr": "delhi",
  "Delhi": "delhi",
  "Bengaluru": "bengaluru",
  "Pune": "pune",
  "Hyderabad": "hyderabad",
  "Chennai": "chennai",
  "Kolkata": "kolkata",
  "Ahmedabad": "ahmedabad",
  "Jaipur": "jaipur",
  "Chandigarh": "chandigarh",
  "Lucknow": "lucknow",
  "Kochi": "kochi"
}};

// Helper functions for the UI dropdowns
export function getStates() {{
  return Object.keys(INDIA_LOCATIONS).sort();
}}

export function getDistricts(state: string) {{
  if (!state || !(state in INDIA_LOCATIONS)) return [];
  return Object.keys(INDIA_LOCATIONS[state as keyof typeof INDIA_LOCATIONS]).sort();
}}

export function getCities(state: string, district: string) {{
  if (!state || !(state in INDIA_LOCATIONS)) return [];
  const stateData = INDIA_LOCATIONS[state as keyof typeof INDIA_LOCATIONS];
  if (!district || !(district in stateData)) return [];
  return Object.keys(stateData[district as keyof typeof stateData]).sort();
}}

export function getLocalities(state: string, district: string, city: string) {{
  if (!state || !(state in INDIA_LOCATIONS)) return [];
  const stateData = INDIA_LOCATIONS[state as keyof typeof INDIA_LOCATIONS];
  if (!district || !(district in stateData)) return [];
  const districtData = stateData[district as keyof typeof stateData];
  if (!city || !(city in districtData)) return [];
  return [...districtData[city as keyof typeof districtData]].sort();
}}
"""

with open('src/data/indiaLocations.ts', 'w', encoding='utf-8') as f:
    f.write(ts_content)

print('Successfully generated indiaLocations.ts')
