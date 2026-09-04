import { createFileRoute, redirect } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { IndianRupee, LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
  AMENITIES,
  DEFAULT_SPECS,
  formatINR,
  getCity,
  isValidPrediction,
  predict as localPredict,
  type AgeBand,
  type AmenityKey,
  type Furnishing,
  type Prediction,
  type PropertyType,
  type Specs,
} from "@/lib/kimat/model";
import { fetchPrediction, apiResponseToPrediction } from "@/lib/kimat/api";
import { LocationSelector } from "@/components/kimat/LocationSelector";
import { LOCATION_TO_CITY_ID } from "@/data/indiaLocations";
import { EstimateCard } from "@/components/kimat/EstimateCard";
import { DriversPanel } from "@/components/kimat/DriversPanel";
import { TrendChart } from "@/components/kimat/TrendChart";
import { CompareMode } from "@/components/kimat/CompareMode";
import { WhatIf } from "@/components/kimat/WhatIf";
import { ThemeToggle } from "@/components/kimat/ThemeToggle";
import { Chips, Field, RangeSlider, Stepper, ToggleChips } from "@/components/kimat/controls";

const TITLE = "Kimat — India House Price Prediction";
const DESCRIPTION =
  "Estimate what a home is worth across 12 Indian cities. Live ML-backed price predictions with a confidence range, factor breakdown and city-to-city comparison.";

export const Route = createFileRoute("/")({
  beforeLoad: () => {
    if (typeof window !== "undefined") {
      const isAuth = localStorage.getItem("token") !== null;
      if (!isAuth) {
        throw redirect({ to: "/login" });
      }
    }
  },
  head: () => ({
    meta: [
      { title: TITLE },
      { name: "description", content: DESCRIPTION },
      { property: "og:title", content: TITLE },
      { property: "og:description", content: DESCRIPTION },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Kimat,
});

function Section({
  title,
  children,
  eyebrow,
}: {
  title: string;
  eyebrow?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="panel p-6" id={`section-${eyebrow?.toLowerCase().replace(/\s/g, "-")}`}>
      {eyebrow ? <div className="label-eyebrow">{eyebrow}</div> : null}
      <h2 className="mb-5 mt-1 text-xl font-semibold text-foreground">{title}</h2>
      {children}
    </section>
  );
}

function Kimat() {
  const { logout, user, isLoading } = useAuth();
  const [specs, setSpecs] = useState<Specs>(DEFAULT_SPECS);
  const [compareCityId, setCompareCityId] = useState("mumbai");

  // ---------------------------------------------------------------------------
  // Backend prediction state
  // The main estimate card is driven by the FastAPI backend.
  // WhatIf / CompareMode / TrendChart continue to use the local model for
  // instant interactivity (no network round-trip for every slider tick).
  // ---------------------------------------------------------------------------
  const [apiPrediction, setApiPrediction] = useState<Prediction | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [apiLoading, setApiLoading] = useState(false);

  // Debounce backend calls: wait 400 ms after the user stops changing sliders.
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const requestPrediction = useCallback((currentSpecs: Specs) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setApiLoading(true);
      setApiError(null);
      try {
        const response = await fetchPrediction(currentSpecs);
        setApiPrediction(apiResponseToPrediction(response, currentSpecs));
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Prediction unavailable";
        setApiError(message);
        // Fall back to local model so the UI is never blank.
        const fallback = localPredict(currentSpecs);
        setApiPrediction(
          isValidPrediction(fallback)
            ? fallback
            : null,
        );
      } finally {
        setApiLoading(false);
      }
    }, 400);
  }, []);

  // Trigger a backend call whenever specs change.
  useEffect(() => {
    requestPrediction(specs);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [specs, requestPrediction]);

  // While waiting for the first API response use the local model as a placeholder.
  const localFallback = useMemo(() => localPredict(specs), [specs]);
  const prediction: Prediction = apiPrediction ?? localFallback;

  const city = getCity(specs.cityId);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  const update = <K extends keyof Specs>(key: K, value: Specs[K]) =>
    setSpecs((s) => ({ ...s, [key]: value }));

  const handleLocationChange = (key: keyof Specs, val: string) => {
    setSpecs((s) => {
      const next = { ...s, [key]: val };
      if (key === "state") {
        next.district = "";
        next.city = "";
        next.locality = "";
        next.cityId = "";
      } else if (key === "district") {
        next.city = "";
        next.locality = "";
        next.cityId = "";
      } else if (key === "city") {
        next.locality = "";
        next.cityId = LOCATION_TO_CITY_ID[val] ?? "";
      }
      return next;
    });
  };

  const handleLocationContinue = () => {
    document.getElementById("section-step-02")?.scrollIntoView({ behavior: "smooth" });
  };

  const toggleAmenity = (key: AmenityKey) =>
    setSpecs((s) => ({
      ...s,
      amenities: s.amenities.includes(key)
        ? s.amenities.filter((a) => a !== key)
        : [...s.amenities, key],
    }));

  return (
    <div className="min-h-screen bg-background">
      <header className="no-print sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-accent-foreground">
              <IndianRupee className="h-4 w-4" />
            </span>
            <div>
              <div className="font-display text-lg font-bold leading-none">Kimat</div>
              <div className="text-[0.68rem] text-muted-foreground">India home value engine</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <button
              onClick={logout}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-input bg-background px-4 py-2 text-sm font-medium text-foreground shadow-sm transition-all hover:bg-accent/50 hover:shadow-md active:scale-[0.98]"
              title={`Logged in as ${user?.name}`}
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 pb-20 pt-8">
        <div className="grain rounded-3xl border border-border p-8">
          <h1 className="max-w-2xl font-display text-4xl font-bold leading-tight sm:text-5xl">
            What is this home actually worth?
          </h1>
          <p className="mt-3 max-w-xl text-muted-foreground">
            A gradient-boosted model trained on multi-city Indian listings prices your property live
            — with the reasoning shown, not hidden.
          </p>
          <div className="mt-6 flex flex-wrap gap-6 font-mono text-xs text-muted-foreground">
            <span>12 cities</span>
            <span>R² 0.912 · RMSE ₹6.4L</span>
            <span>±5.5% confidence band</span>
          </div>
        </div>

        {/* Backend error banner — shown if API call fails but local fallback is active */}
        {apiError && (
          <div className="mt-4 rounded-xl border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-700 dark:text-yellow-300">
            <strong>Note:</strong> Showing local estimate — backend unavailable ({apiError}). Start
            the FastAPI server to get ML-model predictions.
          </div>
        )}

        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_23rem]">
          <div className="space-y-6">
            <LocationSelector
              value={{
                state: specs.state,
                district: specs.district,
                city: specs.city,
                locality: specs.locality,
              }}
              onChange={handleLocationChange}
              onContinue={handleLocationContinue}
            />

            <Section eyebrow="Step 02" title="Property specifications">
              <div className="grid gap-6 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <Field label="Carpet area" hint={`${specs.area} sq.ft`}>
                    <RangeSlider
                      value={specs.area}
                      min={300}
                      max={5000}
                      step={25}
                      onChange={(v) => update("area", v)}
                    />
                  </Field>
                </div>
                <Field label="Bedrooms (BHK)">
                  <Stepper value={specs.bhk} min={1} max={8} onChange={(v) => update("bhk", v)} />
                </Field>
                <Field label="Bathrooms">
                  <Stepper
                    value={specs.bathrooms}
                    min={1}
                    max={8}
                    onChange={(v) => update("bathrooms", v)}
                  />
                </Field>
                {specs.propertyType !== "plot" && (
                  <Field label={specs.propertyType === "apartment" ? "Floor" : "Total floors"}>
                    <Stepper
                      value={specs.propertyType === "apartment" ? specs.floor : specs.totalFloors}
                      min={specs.propertyType === "apartment" ? 0 : 1}
                      max={specs.propertyType === "apartment" ? specs.totalFloors : 60}
                      onChange={(v) => {
                        if (specs.propertyType === "apartment") {
                          update("floor", v);
                        } else {
                          update("totalFloors", v);
                          update("floor", 0);
                        }
                      }}
                    />
                  </Field>
                )}
                {specs.propertyType === "apartment" && (
                  <Field label="Total floors">
                    <Stepper
                      value={specs.totalFloors}
                      min={1}
                      max={60}
                      onChange={(v) => {
                        update("totalFloors", v);
                        if (specs.floor > v) update("floor", v);
                      }}
                    />
                  </Field>
                )}
                <div className="sm:col-span-2">
                  <Field label="Property type">
                    <Chips<PropertyType>
                      options={[
                        { value: "apartment", label: "Apartment" },
                        { value: "villa", label: "Villa" },
                        { value: "independent", label: "Independent house" },
                        { value: "plot", label: "Plot" },
                      ]}
                      value={specs.propertyType}
                      onChange={(v) => {
                        setSpecs((s) => {
                          const next = { ...s, propertyType: v };
                          if (v === "apartment") {
                            next.totalFloors =
                              s.totalFloors > 1 ? s.totalFloors : DEFAULT_SPECS.totalFloors;
                            if (next.floor > next.totalFloors) next.floor = next.totalFloors;
                          } else if (v === "plot") {
                            next.floor = 0;
                            next.totalFloors = 0;
                          } else {
                            next.floor = 0;
                            if (s.propertyType === "apartment") {
                              next.totalFloors = Math.max(1, s.floor || 1);
                            }
                          }
                          return next;
                        });
                      }}
                    />
                  </Field>
                </div>
                <Field label="Furnishing">
                  <Chips<Furnishing>
                    options={[
                      { value: "unfurnished", label: "Unfurnished" },
                      { value: "semi", label: "Semi" },
                      { value: "full", label: "Full" },
                    ]}
                    value={specs.furnishing}
                    onChange={(v) => update("furnishing", v)}
                  />
                </Field>
                <Field label="Property age">
                  <Chips<AgeBand>
                    options={[
                      { value: "new", label: "New" },
                      { value: "1-5", label: "1–5 yrs" },
                      { value: "5-10", label: "5–10 yrs" },
                      { value: "10-20", label: "10–20 yrs" },
                      { value: "20+", label: "20+ yrs" },
                    ]}
                    value={specs.age}
                    onChange={(v) => update("age", v)}
                  />
                </Field>
                <div className="sm:col-span-2">
                  <Field label="Amenities">
                    <ToggleChips<AmenityKey>
                      options={AMENITIES.map((a) => ({ value: a.key, label: a.label }))}
                      values={specs.amenities}
                      onToggle={toggleAmenity}
                    />
                  </Field>
                </div>
              </div>
            </Section>

            <Section eyebrow="Explainability" title="What's driving this price">
              <DriversPanel drivers={prediction.drivers} />
            </Section>

            <Section eyebrow="Market" title={`${city.name} price trend`}>
              <TrendChart cityId={specs.cityId} />
            </Section>

            <div className="grid gap-6 md:grid-cols-2">
              <Section eyebrow="Comparison" title="Same home, another city">
                <CompareMode
                  specs={specs}
                  compareCityId={compareCityId === specs.cityId ? "delhi" : compareCityId}
                  onCompareCity={setCompareCityId}
                />
              </Section>
              <Section eyebrow="What-if" title="Price sensitivity">
                <WhatIf specs={specs} />
              </Section>
            </div>
          </div>

          <aside className="lg:sticky lg:top-24 lg:self-start">
            <EstimateCard
              prediction={prediction}
              specs={specs}
              cityName={city.name}
              onDownload={() => window.print()}
              isLoading={apiLoading && apiPrediction === null}
            />
            <p className="mt-3 px-1 text-[0.7rem] leading-relaxed text-muted-foreground">
              Estimates are model output on aggregated market data, not a valuation or an offer.
              Range shown is the {(prediction.confidence * 100).toFixed(1)}% prediction interval
              around {formatINR(prediction.price)}.
            </p>
          </aside>
        </div>
      </main>
    </div>
  );
}
