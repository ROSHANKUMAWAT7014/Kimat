"""
Ground-truth city/locality rate tables.

These are ported 1:1 from the frontend's src/lib/kimat/model.ts so that the
synthetic dataset we train on is consistent with the numbers already shown
in the UI (city grid, ₹/sq.ft badges, etc). If you plug in a real dataset
later, this file becomes reference/seed data only.
"""

CITIES = {
    "mumbai":     {"state": "Maharashtra",  "base_rate": 28400, "yoy": 0.081,
                    "localities": {"Andheri West": 1.06, "Bandra": 1.62, "Powai": 1.12,
                                   "Thane": 0.61, "Navi Mumbai": 0.58, "Borivali": 0.82}},
    "delhi":      {"state": "Delhi",        "base_rate": 17600, "yoy": 0.068,
                    "localities": {"South Delhi": 1.55, "Dwarka": 0.83, "Gurugram": 1.14,
                                   "Noida": 0.76, "Greater Noida": 0.52, "Rohini": 0.79}},
    "bengaluru":  {"state": "Karnataka",    "base_rate": 11200, "yoy": 0.094,
                    "localities": {"Indiranagar": 1.48, "Koramangala": 1.44, "Whitefield": 0.92,
                                   "Electronic City": 0.71, "Hebbal": 1.02, "Sarjapur Road": 0.96}},
    "pune":       {"state": "Maharashtra",  "base_rate": 9400,  "yoy": 0.077,
                    "localities": {"Koregaon Park": 1.52, "Baner": 1.14, "Hinjewadi": 0.88,
                                   "Kharadi": 1.05, "Wakad": 0.93, "Hadapsar": 0.84}},
    "hyderabad":  {"state": "Telangana",    "base_rate": 8100,  "yoy": 0.089,
                    "localities": {"Banjara Hills": 1.58, "Gachibowli": 1.18, "Hitec City": 1.24,
                                   "Kondapur": 1.02, "Miyapur": 0.74, "Uppal": 0.66}},
    "chennai":    {"state": "Tamil Nadu",   "base_rate": 8600,  "yoy": 0.058,
                    "localities": {"Adyar": 1.46, "Anna Nagar": 1.28, "Velachery": 0.96,
                                   "OMR": 0.88, "Porur": 0.79, "Tambaram": 0.64}},
    "kolkata":    {"state": "West Bengal",  "base_rate": 6900,  "yoy": 0.041,
                    "localities": {"Ballygunge": 1.62, "Salt Lake": 1.16, "New Town": 0.94,
                                   "Behala": 0.72, "Howrah": 0.63, "Garia": 0.78}},
    "ahmedabad":  {"state": "Gujarat",      "base_rate": 5400,  "yoy": 0.063,
                    "localities": {"Satellite": 1.32, "Bopal": 0.96, "SG Highway": 1.18,
                                   "Maninagar": 0.81, "Chandkheda": 0.74, "Vastrapur": 1.24}},
    "jaipur":     {"state": "Rajasthan",    "base_rate": 4600,  "yoy": 0.055,
                    "localities": {"C-Scheme": 1.64, "Malviya Nagar": 1.22, "Vaishali Nagar": 1.04,
                                   "Mansarovar": 0.92, "Jagatpura": 0.81, "Ajmer Road": 0.70}},
    "chandigarh": {"state": "Chandigarh",   "base_rate": 9800,  "yoy": 0.049,
                    "localities": {"Sector 8": 1.48, "Sector 22": 1.12, "Mohali": 0.74,
                                   "Panchkula": 0.82, "Zirakpur": 0.60, "IT Park": 1.06}},
    "lucknow":    {"state": "Uttar Pradesh","base_rate": 4300,  "yoy": 0.052,
                    "localities": {"Gomti Nagar": 1.38, "Hazratganj": 1.26, "Indira Nagar": 1.00,
                                   "Aliganj": 0.94, "Jankipuram": 0.78, "Raebareli Road": 0.68}},
    "kochi":      {"state": "Kerala",       "base_rate": 5900,  "yoy": 0.060,
                    "localities": {"Marine Drive": 1.54, "Panampilly Nagar": 1.36, "Kakkanad": 0.92,
                                   "Edappally": 0.98, "Aluva": 0.72, "Fort Kochi": 1.08}},
}

TYPE_MULT = {"apartment": 1.00, "villa": 1.34, "independent": 1.16, "plot": 0.72}
FURNISH_MULT = {"unfurnished": 1.00, "semi": 1.06, "full": 1.13}

# age band -> (years_min, years_max, multiplier)
AGE_BANDS = {
    "new":   (0, 1,  1.09),
    "1-5":   (1, 5,  1.02),
    "5-10":  (5, 10, 0.95),
    "10-20": (10, 20, 0.87),
    "20+":   (20, 40, 0.78),
}

AMENITIES = {
    "parking": 0.035, "lift": 0.018, "security": 0.026, "power_backup": 0.021,
    "gym": 0.022, "pool": 0.031, "clubhouse": 0.024, "garden": 0.016,
}

PROPERTY_TYPES = list(TYPE_MULT.keys())
FURNISHING_STATUSES = list(FURNISH_MULT.keys())
AGE_BAND_LABELS = list(AGE_BANDS.keys())
AMENITY_KEYS = list(AMENITIES.keys())
