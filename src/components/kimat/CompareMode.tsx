import { CITIES, formatINR, getCity, predict, type Specs } from "@/lib/kimat/model";

export function CompareMode({
  specs,
  compareCityId,
  onCompareCity,
}: {
  specs: Specs;
  compareCityId: string;
  onCompareCity: (id: string) => void;
}) {
  const cityA = getCity(specs.cityId);
  const cityB = getCity(compareCityId);
  const a = predict(specs);
  const bSpecs: Specs = {
    ...specs,
    cityId: cityB.id,
    locality: cityB.localities[Math.min(2, cityB.localities.length - 1)]?.name ?? "",
  };
  const b = predict(bSpecs);
  const diff = ((a.price - b.price) / b.price) * 100;
  const maxPrice = Math.max(a.price, b.price);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="label-eyebrow">Compare against</span>
        <select
          value={compareCityId}
          onChange={(e) => onCompareCity(e.target.value)}
          className="rounded-lg border border-border bg-surface px-3 py-1.5 text-sm text-foreground"
        >
          {CITIES.filter((c) => c.id !== specs.cityId).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {[
        { city: cityA.name, locality: specs.locality, p: a.price, accent: true },
        { city: cityB.name, locality: bSpecs.locality, p: b.price, accent: false },
      ].map((row) => (
        <div key={row.city} className="space-y-1.5">
          <div className="flex items-baseline justify-between text-sm">
            <span className="font-medium text-foreground">
              {row.city}
              <span className="ml-2 text-xs text-muted-foreground">{row.locality}</span>
            </span>
            <span className="font-mono tabular-nums">{formatINR(row.p)}</span>
          </div>
          <div className="h-2.5 rounded-full bg-surface-2">
            <div
              className={`h-full rounded-full transition-all duration-500 ${row.accent ? "bg-accent" : "bg-chart-3"}`}
              style={{ width: `${(row.p / maxPrice) * 100}%` }}
            />
          </div>
        </div>
      ))}

      <p className="rounded-xl bg-surface-2 p-3 text-sm text-foreground">
        The same {specs.bhk} BHK, {specs.area} sq.ft home is{" "}
        <strong className={diff >= 0 ? "text-clay" : "text-jade"}>
          {Math.abs(diff).toFixed(1)}% {diff >= 0 ? "more" : "less"} expensive
        </strong>{" "}
        in {cityA.name} than in {cityB.name}.
      </p>
    </div>
  );
}
