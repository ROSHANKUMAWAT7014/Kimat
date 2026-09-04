import { Minus, Plus } from "lucide-react";
import type { ReactNode } from "react";

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <span className="label-eyebrow">{label}</span>
        {hint ? <span className="font-mono text-xs text-foreground">{hint}</span> : null}
      </div>
      {children}
    </div>
  );
}

export function Stepper({
  value,
  min,
  max,
  onChange,
  suffix,
}: {
  value: number;
  min: number;
  max: number;
  onChange: (v: number) => void;
  suffix?: string;
}) {
  const set = (v: number) => onChange(Math.min(max, Math.max(min, v)));
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        aria-label="Decrease"
        onClick={() => set(value - 1)}
        className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface transition-colors hover:bg-surface-2 disabled:opacity-40"
        disabled={value <= min}
      >
        <Minus className="h-3.5 w-3.5" />
      </button>
      <div className="min-w-14 rounded-lg bg-surface-2 px-3 py-1.5 text-center font-mono text-sm">
        {value}
        {suffix ? <span className="text-muted-foreground"> {suffix}</span> : null}
      </div>
      <button
        type="button"
        aria-label="Increase"
        onClick={() => set(value + 1)}
        className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface transition-colors hover:bg-surface-2 disabled:opacity-40"
        disabled={value >= max}
      >
        <Plus className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export function Chips<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          onClick={() => onChange(o.value)}
          className={[
            "rounded-full border px-3 py-1.5 text-xs font-medium transition-all duration-200",
            o.value === value
              ? "border-accent bg-accent text-accent-foreground"
              : "border-border bg-surface text-muted-foreground hover:border-accent/50 hover:text-foreground",
          ].join(" ")}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function ToggleChips<T extends string>({
  options,
  values,
  onToggle,
}: {
  options: { value: T; label: string }[];
  values: T[];
  onToggle: (v: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => {
        const on = values.includes(o.value);
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={on}
            onClick={() => onToggle(o.value)}
            className={[
              "rounded-full border px-3 py-1.5 text-xs font-medium transition-all duration-200",
              on
                ? "border-jade bg-jade/15 text-foreground"
                : "border-border bg-surface text-muted-foreground hover:border-jade/50",
            ].join(" ")}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

export function RangeSlider({
  value,
  min,
  max,
  step,
  onChange,
}: {
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <input
      type="range"
      value={value}
      min={min}
      max={max}
      step={step}
      onChange={(e) => onChange(Number(e.target.value))}
      className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-surface-2 accent-accent"
    />
  );
}
