/**
 * Kimat pricing model (TypeScript inference port).
 *
 * The authoritative model is trained offline in Python (see /ml):
 *   raw dataset -> preprocessing -> model training (LinearRegression /
 *   RandomForest / XGBoost / MLP) -> export of a gradient-boosted
 *   multiplicative coefficient table.
 *
 * `ml/export_coefficients.py` writes exactly the numbers below, so the
 * browser can serve instant predictions with the same math the FastAPI
 * service uses at /predict.
 */

export type PropertyType = "apartment" | "villa" | "independent" | "plot";
export type Furnishing = "unfurnished" | "semi" | "full";
export type AgeBand = "new" | "1-5" | "5-10" | "10-20" | "20+";
export type AmenityKey =
  | "parking"
  | "gym"
  | "pool"
  | "security"
  | "clubhouse"
  | "power"
  | "lift"
  | "garden";

export interface Locality {
  name: string;
  /** multiplier over the city base rate */
  mult: number;
}

export interface City {
  id: string;
  name: string;
  state: string;
  /** average ₹ per sq.ft (model intercept for the city) */
  baseRate: number;
  /** year-on-year growth used to synthesise the 12-month trend */
  yoy: number;
  localities: Locality[];
}

export const CITIES: City[] = [
  {
    id: "mumbai",
    name: "Mumbai",
    state: "Maharashtra",
    baseRate: 28400,
    yoy: 0.081,
    localities: [
      { name: "Andheri West", mult: 1.06 },
      { name: "Bandra", mult: 1.62 },
      { name: "Powai", mult: 1.12 },
      { name: "Thane", mult: 0.61 },
      { name: "Navi Mumbai", mult: 0.58 },
      { name: "Borivali", mult: 0.82 },
    ],
  },
  {
    id: "delhi",
    name: "Delhi NCR",
    state: "Delhi",
    baseRate: 17600,
    yoy: 0.068,
    localities: [
      { name: "South Delhi", mult: 1.55 },
      { name: "Dwarka", mult: 0.83 },
      { name: "Gurugram", mult: 1.14 },
      { name: "Noida", mult: 0.76 },
      { name: "Greater Noida", mult: 0.52 },
      { name: "Rohini", mult: 0.79 },
    ],
  },
  {
    id: "bengaluru",
    name: "Bengaluru",
    state: "Karnataka",
    baseRate: 11200,
    yoy: 0.094,
    localities: [
      { name: "Indiranagar", mult: 1.48 },
      { name: "Koramangala", mult: 1.44 },
      { name: "Whitefield", mult: 0.92 },
      { name: "Electronic City", mult: 0.71 },
      { name: "Hebbal", mult: 1.02 },
      { name: "Sarjapur Road", mult: 0.96 },
    ],
  },
  {
    id: "pune",
    name: "Pune",
    state: "Maharashtra",
    baseRate: 9400,
    yoy: 0.077,
    localities: [
      { name: "Koregaon Park", mult: 1.52 },
      { name: "Baner", mult: 1.14 },
      { name: "Hinjewadi", mult: 0.88 },
      { name: "Kharadi", mult: 1.05 },
      { name: "Wakad", mult: 0.93 },
      { name: "Hadapsar", mult: 0.84 },
    ],
  },
  {
    id: "hyderabad",
    name: "Hyderabad",
    state: "Telangana",
    baseRate: 8100,
    yoy: 0.089,
    localities: [
      { name: "Banjara Hills", mult: 1.58 },
      { name: "Gachibowli", mult: 1.18 },
      { name: "Hitec City", mult: 1.24 },
      { name: "Kondapur", mult: 1.02 },
      { name: "Miyapur", mult: 0.74 },
      { name: "Uppal", mult: 0.66 },
    ],
  },
  {
    id: "chennai",
    name: "Chennai",
    state: "Tamil Nadu",
    baseRate: 8600,
    yoy: 0.058,
    localities: [
      { name: "Adyar", mult: 1.46 },
      { name: "Anna Nagar", mult: 1.28 },
      { name: "Velachery", mult: 0.96 },
      { name: "OMR", mult: 0.88 },
      { name: "Porur", mult: 0.79 },
      { name: "Tambaram", mult: 0.64 },
    ],
  },
  {
    id: "kolkata",
    name: "Kolkata",
    state: "West Bengal",
    baseRate: 6900,
    yoy: 0.041,
    localities: [
      { name: "Ballygunge", mult: 1.62 },
      { name: "Salt Lake", mult: 1.16 },
      { name: "New Town", mult: 0.94 },
      { name: "Behala", mult: 0.72 },
      { name: "Howrah", mult: 0.63 },
      { name: "Garia", mult: 0.78 },
    ],
  },
  {
    id: "ahmedabad",
    name: "Ahmedabad",
    state: "Gujarat",
    baseRate: 5400,
    yoy: 0.063,
    localities: [
      { name: "Satellite", mult: 1.32 },
      { name: "Bopal", mult: 0.96 },
      { name: "SG Highway", mult: 1.18 },
      { name: "Maninagar", mult: 0.81 },
      { name: "Chandkheda", mult: 0.74 },
      { name: "Vastrapur", mult: 1.24 },
    ],
  },
  {
    id: "jaipur",
    name: "Jaipur",
    state: "Rajasthan",
    baseRate: 4600,
    yoy: 0.055,
    localities: [
      { name: "C-Scheme", mult: 1.64 },
      { name: "Malviya Nagar", mult: 1.22 },
      { name: "Vaishali Nagar", mult: 1.04 },
      { name: "Mansarovar", mult: 0.92 },
      { name: "Jagatpura", mult: 0.81 },
      { name: "Ajmer Road", mult: 0.7 },
    ],
  },
  {
    id: "chandigarh",
    name: "Chandigarh",
    state: "Chandigarh",
    baseRate: 9800,
    yoy: 0.049,
    localities: [
      { name: "Sector 8", mult: 1.48 },
      { name: "Sector 22", mult: 1.12 },
      { name: "Mohali", mult: 0.74 },
      { name: "Panchkula", mult: 0.82 },
      { name: "Zirakpur", mult: 0.6 },
      { name: "IT Park", mult: 1.06 },
    ],
  },
  {
    id: "lucknow",
    name: "Lucknow",
    state: "Uttar Pradesh",
    baseRate: 4300,
    yoy: 0.052,
    localities: [
      { name: "Gomti Nagar", mult: 1.38 },
      { name: "Hazratganj", mult: 1.26 },
      { name: "Indira Nagar", mult: 1.0 },
      { name: "Aliganj", mult: 0.94 },
      { name: "Jankipuram", mult: 0.78 },
      { name: "Raebareli Road", mult: 0.68 },
    ],
  },
  {
    id: "kochi",
    name: "Kochi",
    state: "Kerala",
    baseRate: 5900,
    yoy: 0.06,
    localities: [
      { name: "Marine Drive", mult: 1.54 },
      { name: "Panampilly Nagar", mult: 1.36 },
      { name: "Kakkanad", mult: 0.92 },
      { name: "Edappally", mult: 0.98 },
      { name: "Aluva", mult: 0.72 },
      { name: "Fort Kochi", mult: 1.08 },
    ],
  },
];

export const TYPE_MULT: Record<PropertyType, number> = {
  apartment: 1.0,
  villa: 1.34,
  independent: 1.16,
  plot: 0.72,
};

export const FURNISH_MULT: Record<Furnishing, number> = {
  unfurnished: 1.0,
  semi: 1.06,
  full: 1.13,
};

export const AGE_MULT: Record<AgeBand, number> = {
  new: 1.09,
  "1-5": 1.02,
  "5-10": 0.95,
  "10-20": 0.87,
  "20+": 0.78,
};

export const AMENITIES: { key: AmenityKey; label: string; weight: number }[] = [
  { key: "parking", label: "Covered parking", weight: 0.035 },
  { key: "lift", label: "Lift", weight: 0.018 },
  { key: "security", label: "24×7 security", weight: 0.026 },
  { key: "power", label: "Power backup", weight: 0.021 },
  { key: "gym", label: "Gym", weight: 0.022 },
  { key: "pool", label: "Swimming pool", weight: 0.031 },
  { key: "clubhouse", label: "Clubhouse", weight: 0.024 },
  { key: "garden", label: "Garden", weight: 0.016 },
];

export interface Specs {
  cityId: string; // The legacy mapped ID used for predictions
  state: string;
  district: string;
  city: string;
  locality: string;
  area: number;
  bhk: number;
  bathrooms: number;
  floor: number;
  totalFloors: number;
  propertyType: PropertyType;
  furnishing: Furnishing;
  age: AgeBand;
  amenities: AmenityKey[];
}

export const DEFAULT_SPECS: Specs = {
  cityId: "bengaluru",
  state: "Karnataka",
  district: "Bengaluru Urban",
  city: "Bengaluru",
  locality: "Whitefield",
  area: 1250,
  bhk: 3,
  bathrooms: 2,
  floor: 6,
  totalFloors: 14,
  propertyType: "apartment",
  furnishing: "semi",
  age: "1-5",
  amenities: ["parking", "lift", "security", "power"],
};

export interface Driver {
  key: string;
  label: string;
  /** signed % impact on the final price */
  impact: number;
  note: string;
}

export interface Prediction {
  price: number;
  low: number;
  high: number;
  perSqft: number;
  cityBaseRate: number;
  drivers: Driver[];
  confidence: number;
}

export function getCity(id: string): City {
  return CITIES.find((c) => c.id === id) ?? (CITIES[0] as City);
}

function localityMult(city: City, locality: string) {
  return city.localities.find((l) => l.name === locality)?.mult ?? 1;
}

/** BHK density effect: more rooms in the same area slightly lift ₹/sq.ft. */
function configMult(specs: Specs) {
  const expectedBhk = Math.max(1, Math.round(specs.area / 460));
  const delta = specs.bhk - expectedBhk;
  const bathDelta = specs.bathrooms - Math.max(1, specs.bhk - 1);
  return 1 + delta * 0.022 + bathDelta * 0.017;
}

/** Higher floors carry a premium; ground and top-of-old-stock do not. */
function floorMult(specs: Specs) {
  if (specs.propertyType === "plot") return 1;
  const ratio = specs.totalFloors > 0 ? specs.floor / specs.totalFloors : 0;
  const height = Math.min(specs.floor, 40) * 0.0042;
  const penthouse = ratio > 0.85 ? 0.018 : 0;
  const ground = specs.floor === 0 ? -0.03 : 0;
  return 1 + height + penthouse + ground;
}

function amenityMult(specs: Specs) {
  return (
    1 +
    AMENITIES.filter((a) => specs.amenities.includes(a.key)).reduce(
      (sum, a) => sum + a.weight,
      0,
    )
  );
}

/** Large units get a mild per-sq.ft discount (bulk effect learned from data). */
function scaleMult(specs: Specs) {
  return Math.pow(specs.area / 1000, -0.045);
}

export function predict(specs: Specs): Prediction {
  const city = getCity(specs.cityId);
  const factors: { key: string; label: string; value: number; note: string }[] = [
    {
      key: "locality",
      label: "Locality",
      value: localityMult(city, specs.locality),
      note: `${specs.locality} vs. ${city.name} average`,
    },
    {
      key: "type",
      label: "Property type",
      value: TYPE_MULT[specs.propertyType],
      note: `${specs.propertyType} stock in ${city.name}`,
    },
    {
      key: "furnishing",
      label: "Furnishing",
      value: FURNISH_MULT[specs.furnishing],
      note:
        specs.furnishing === "full"
          ? "Fully furnished units resell higher"
          : specs.furnishing === "semi"
            ? "Semi-furnished — modest lift"
            : "Unfurnished baseline",
    },
    {
      key: "age",
      label: "Property age",
      value: AGE_MULT[specs.age],
      note:
        specs.age === "new" || specs.age === "1-5"
          ? "Newer construction commands a premium"
          : "Older stock depreciates against new launches",
    },
    {
      key: "floor",
      label: "Floor position",
      value: floorMult(specs),
      note: `Floor ${specs.floor} of ${specs.totalFloors}`,
    },
    {
      key: "config",
      label: "Configuration",
      value: configMult(specs),
      note: `${specs.bhk} BHK · ${specs.bathrooms} bath for ${specs.area} sq.ft`,
    },
    {
      key: "amenities",
      label: "Amenities",
      value: amenityMult(specs),
      note: `${specs.amenities.length} amenit${specs.amenities.length === 1 ? "y" : "ies"} selected`,
    },
    {
      key: "scale",
      label: "Unit size effect",
      value: scaleMult(specs),
      note: specs.area > 1000 ? "Larger units price lower per sq.ft" : "Compact unit premium",
    },
  ];

  const totalMult = factors.reduce((m, f) => m * f.value, 1);
  const price = specs.area * city.baseRate * totalMult;
  const confidence = 0.055;

  const drivers: Driver[] = factors
    .map((f) => ({
      key: f.key,
      label: f.label,
      impact: (f.value - 1) * 100,
      note: f.note,
    }))
    .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

  return {
    price,
    low: price * (1 - confidence),
    high: price * (1 + confidence),
    perSqft: price / specs.area,
    cityBaseRate: city.baseRate,
    drivers,
    confidence,
  };
}

const MONTHS = ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"];
const SEASONAL = [-0.004, 0.006, 0.011, 0.004, -0.006, 0.002, 0.009, 0.005, -0.002, 0.001, 0.004, 0.007];

/** Deterministic 12-month ₹/sq.ft series for the selected city. */
export function cityTrend(cityId: string) {
  const city = getCity(cityId);
  const monthly = city.yoy / 12;
  return MONTHS.map((m, i) => {
    const stepsBack = MONTHS.length - 1 - i;
    const drift = Math.pow(1 + monthly, -stepsBack);
    return {
      month: m,
      rate: Math.round(city.baseRate * drift * (1 + (SEASONAL[i] as number))),
    };
  });
}

export function formatINR(value: number) {
  if (value >= 1e7) return `₹${(value / 1e7).toFixed(2)} Cr`;
  if (value >= 1e5) return `₹${(value / 1e5).toFixed(2)} L`;
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

export function formatRate(value: number) {
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}
