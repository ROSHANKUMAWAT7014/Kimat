import { useEffect, useRef, useState } from "react";
import { Download, TrendingUp } from "lucide-react";
import { formatINR, formatRate, type Prediction, type Specs } from "@/lib/kimat/model";

/** Smoothly animates a number toward its target — the signature odometer. */
function useOdometer(target: number, duration = 650) {
  const [display, setDisplay] = useState(target);
  const fromRef = useRef(target);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const from = fromRef.current;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const v = from + (target - from) * eased;
      setDisplay(v);
      fromRef.current = v;
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return display;
}

export function EstimateCard({
  prediction,
  specs,
  cityName,
  onDownload,
  isLoading = false,
}: {
  prediction: Prediction;
  specs: Specs;
  cityName: string;
  onDownload: () => void;
  isLoading?: boolean;
}) {
  const price = useOdometer(prediction.price);
  const rate = useOdometer(prediction.perSqft);

  return (
    <div className="panel grain overflow-hidden">
      <div className="border-b border-border px-6 py-4">
        <div className="label-eyebrow">Live estimate</div>
        <div className="mt-1 text-sm text-muted-foreground">
          {specs.bhk} BHK {specs.propertyType} · {specs.area} sq.ft · {specs.locality}, {cityName}
        </div>
      </div>

      <div className="px-6 py-6">
        <div className={`font-display text-5xl font-bold tabular-nums tracking-tight text-foreground transition-opacity ${isLoading ? "opacity-50" : "opacity-100"}`}>
          {formatINR(price)}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
          <span className="rounded-full bg-surface-2 px-3 py-1 font-mono text-xs">
            {formatINR(prediction.low)} – {formatINR(prediction.high)}
          </span>
          <span className="text-xs text-muted-foreground">
            ±{(prediction.confidence * 100).toFixed(1)}% confidence band
          </span>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3">
          <div className="rounded-xl bg-surface-2 p-3">
            <div className="label-eyebrow">Effective rate</div>
            <div className="mt-1 font-mono text-lg tabular-nums">{formatRate(rate)}</div>
            <div className="text-[0.7rem] text-muted-foreground">per sq.ft</div>
          </div>
          <div className="rounded-xl bg-surface-2 p-3">
            <div className="label-eyebrow">City average</div>
            <div className="mt-1 font-mono text-lg tabular-nums">
              {formatRate(prediction.cityBaseRate)}
            </div>
            <div className="flex items-center gap-1 text-[0.7rem] text-muted-foreground">
              <TrendingUp className="h-3 w-3" />
              {prediction.perSqft >= prediction.cityBaseRate ? "above" : "below"} city mean
            </div>
          </div>
        </div>

        <button
          onClick={onDownload}
          className="no-print mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-ink px-4 py-2.5 text-sm font-medium text-ink-foreground transition-transform hover:-translate-y-0.5"
        >
          <Download className="h-4 w-4" /> Download report
        </button>
      </div>
    </div>
  );
}
