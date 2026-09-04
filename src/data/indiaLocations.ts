import INDIA_LOCATIONS_RAW from "../../ml/data/KIMAT_DATA/final/india_locations.json?raw";

/**
 * Normalized location database for Pan-India support.
 */
export const INDIA_LOCATIONS = JSON.parse(INDIA_LOCATIONS_RAW);

/**
 * Maps the exact standardized string combination back to the internal `cityId`
 * required by the backend API and local ML coefficients.
 */
export const LOCATION_TO_CITY_ID: Record<string, string> = {
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
};

// Helper functions for the UI dropdowns
export function getStates() {
  return Object.keys(INDIA_LOCATIONS).sort();
}

export function getDistricts(state: string) {
  if (!state || !(state in INDIA_LOCATIONS)) return [];
  return Object.keys(INDIA_LOCATIONS[state as keyof typeof INDIA_LOCATIONS]).sort();
}

export function getCities(state: string, district: string) {
  if (!state || !(state in INDIA_LOCATIONS)) return [];
  const stateData = INDIA_LOCATIONS[state as keyof typeof INDIA_LOCATIONS];
  if (!district || !(district in stateData)) return [];
  return Object.keys(stateData[district as keyof typeof stateData])
    .filter((city) => LOCATION_TO_CITY_ID[city])
    .sort();
}

export function getLocalities(state: string, district: string, city: string) {
  if (!state || !(state in INDIA_LOCATIONS)) return [];
  const stateData = INDIA_LOCATIONS[state as keyof typeof INDIA_LOCATIONS];
  if (!district || !(district in stateData)) return [];
  const districtData = stateData[district as keyof typeof stateData];
  if (!city || !(city in districtData)) return [];
  return [...districtData[city as keyof typeof districtData]].sort();
}
