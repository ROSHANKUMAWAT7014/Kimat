import type { Driver } from "@/lib/kimat/model";

export function DriversPanel({ drivers }: { drivers: Driver[] }) {
  const max = Math.max(12, ...drivers.map((d) => Math.abs(d.impact)));

  return (
    <div className="space-y-3">
      {drivers.map((d) => {
        const width = (Math.abs(d.impact) / max) * 50;
        const positive = d.impact >= 0;
        return (
          <div key={d.key} className="grid grid-cols-[9rem_1fr_4rem] items-center gap-3">
            <div>
              <div className="text-sm font-medium text-foreground">{d.label}</div>
              <div className="text-[0.7rem] leading-tight text-muted-foreground">{d.note}</div>
            </div>
            <div className="relative h-6 rounded-md bg-surface-2">
              <div className="absolute left-1/2 top-0 h-full w-px bg-border" />
              <div
                className={[
                  "absolute top-1 h-4 rounded-sm transition-all duration-500",
                  positive ? "bg-jade" : "bg-clay",
                ].join(" ")}
                style={
                  positive
                    ? { left: "50%", width: `${width}%` }
                    : { right: "50%", width: `${width}%` }
                }
              />
            </div>
            <div
              className={[
                "text-right font-mono text-xs tabular-nums",
                positive ? "text-jade" : "text-clay",
              ].join(" ")}
            >
              {positive ? "+" : ""}
              {d.impact.toFixed(1)}%
            </div>
          </div>
        );
      })}
    </div>
  );
}
