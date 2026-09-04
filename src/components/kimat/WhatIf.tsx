import { useState, useMemo, useEffect } from "react";
import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { formatINR, predict, type Specs } from "@/lib/kimat/model";

type Variable = "area" | "bhk" | "floor";

export function WhatIf({ specs }: { specs: Specs }) {
  const [variable, setVariable] = useState<Variable>("area");
  const [hoveredPoint, setHoveredPoint] = useState<any | null>(null);

  // Fallback if plot is selected
  useEffect(() => {
    if (specs.propertyType === "plot" && variable !== "area") {
      setVariable("area");
    }
  }, [specs.propertyType, variable]);

  const availableVariables = [
    { key: "area" as Variable, label: "Carpet area" },
    ...(specs.propertyType !== "plot" ? [{ key: "bhk" as Variable, label: "Bedrooms" }] : []),
    ...(specs.propertyType !== "plot" ? [{ key: "floor" as Variable, label: "Floor" }] : []),
  ];

  const currentPrice = useMemo(() => predict(specs).price, [specs]);

  const data = useMemo(() => {
    let points: number[] = [];

    if (variable === "area") {
      const current = specs.area;
      points = [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3].map((pct) =>
        Math.max(200, Math.round((current * (1 + pct)) / 50) * 50),
      );
      points.push(current);
    } else if (variable === "bhk") {
      points = [1, 2, 3, 4, 5, 6];
      points.push(specs.bhk);
    } else if (variable === "floor") {
      if (specs.propertyType === "apartment") {
        const maxFloor = specs.totalFloors;
        if (maxFloor <= 10) {
          points = Array.from({ length: maxFloor + 1 }, (_, i) => i);
        } else {
          const step = Math.ceil(maxFloor / 7);
          for (let i = 0; i <= maxFloor; i += step) points.push(i);
          if (points[points.length - 1] !== maxFloor) points.push(maxFloor);
        }
        points.push(specs.floor);
      } else {
        points = [1, 2, 3, 4, 5];
        points.push(specs.totalFloors);
      }
    }

    // Deduplicate and sort
    points = Array.from(new Set(points)).sort((a, b) => a - b);

    return points.map((p) => {
      const next = { ...specs };
      let isCurrent = false;

      if (variable === "area") {
        next.area = p;
        isCurrent = p === specs.area;
      } else if (variable === "bhk") {
        next.bhk = p;
        isCurrent = p === specs.bhk;
      } else if (variable === "floor") {
        if (specs.propertyType === "apartment") {
          next.floor = p;
          isCurrent = p === specs.floor;
        } else {
          next.totalFloors = p;
          next.floor = 0;
          isCurrent = p === specs.totalFloors;
        }
      }

      const pResult = predict(next);
      return {
        x: String(p),
        value: p,
        price: pResult.price,
        isCurrent,
      };
    });
  }, [specs, variable]);

  const activeData = hoveredPoint || data.find((d) => d.isCurrent) || data[0];
  const diff = activeData ? activeData.price - currentPrice : 0;
  const diffPct = activeData ? (diff / currentPrice) * 100 : 0;
  const isPositive = diff > 0;

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 rounded-xl border border-border bg-surface/50 p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-muted-foreground">Current Price</div>
            <div className="font-semibold text-foreground">{formatINR(currentPrice)}</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-muted-foreground">
              Selected: {activeData?.x}{" "}
              {variable === "area" ? "sq.ft" : variable === "bhk" ? "BHK" : "Floor"}
            </div>
            <div className="font-semibold text-foreground">{formatINR(activeData?.price ?? 0)}</div>
          </div>
        </div>

        {Math.abs(diff) > 1 ? (
          <div
            className={`flex justify-end gap-1.5 text-xs font-medium ${
              isPositive ? "text-emerald-500" : "text-rose-500"
            }`}
          >
            <span>{isPositive ? "+" : ""} {formatINR(diff)}</span>
            <span>({isPositive ? "+" : ""}{diffPct.toFixed(1)}%)</span>
          </div>
        ) : (
          <div className="flex justify-end text-xs font-medium text-muted-foreground">No change</div>
        )}
      </div>

      <div className="mb-5 flex flex-wrap items-center gap-2">
        <span className="label-eyebrow mr-1">Sensitivity to</span>
        {availableVariables.map((v) => (
          <button
            key={v.key}
            onClick={() => setVariable(v.key)}
            className={[
              "rounded-full border px-3 py-1.5 text-xs font-medium transition-all",
              v.key === variable
                ? "border-accent bg-accent text-accent-foreground shadow-sm"
                : "border-border bg-surface text-muted-foreground hover:bg-accent/20 hover:text-foreground",
            ].join(" ")}
          >
            {v.label}
          </button>
        ))}
      </div>

      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 12, right: 12, left: -8, bottom: 0 }}
            onMouseMove={(e) => {
              if (e.activePayload && e.activePayload.length > 0) {
                setHoveredPoint(e.activePayload[0].payload);
              }
            }}
            onMouseLeave={() => setHoveredPoint(null)}
          >
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="x"
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              axisLine={false}
              tickLine={false}
              tickMargin={10}
            />
            <YAxis
              domain={["auto", "auto"]}
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => {
                if (v >= 1e7) return `${(v / 1e7).toFixed(1)}Cr`;
                if (v >= 1e5) return `${(v / 1e5).toFixed(1)}L`;
                return `${v}`;
              }}
            />
            <Tooltip
              cursor={{ stroke: "var(--color-border)", strokeWidth: 1, strokeDasharray: "4 4" }}
              content={({ active, payload }) => {
                if (active && payload && payload.length > 0 && payload[0]) {
                  const p = payload[0].payload;
                  const pDiff = p.price - currentPrice;
                  const pDiffPct = (pDiff / currentPrice) * 100;
                  const pIsPos = pDiff > 0;
                  return (
                    <div className="rounded-xl border border-border bg-surface p-3 shadow-lg">
                      <div className="mb-1 text-xs text-muted-foreground">
                        {variable === "area"
                          ? "Carpet Area"
                          : variable === "bhk"
                            ? "Bedrooms"
                            : "Floor"}
                        : <span className="font-medium text-foreground">{p.x}</span>
                      </div>
                      <div className="font-semibold text-foreground">{formatINR(p.price)}</div>
                      {Math.abs(pDiff) > 1 && (
                        <div
                          className={`mt-1 text-[0.65rem] font-medium ${
                            pIsPos ? "text-emerald-500" : "text-rose-500"
                          }`}
                        >
                          {pIsPos ? "+" : ""} {formatINR(pDiff)} ({pIsPos ? "+" : ""}
                          {pDiffPct.toFixed(1)}%)
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke="var(--color-jade)"
              strokeWidth={2}
              animationDuration={400}
              activeDot={{ r: 5, fill: "var(--color-jade)", stroke: "var(--color-background)", strokeWidth: 2 }}
              dot={(props: any) => {
                const { cx, cy, payload } = props;
                if (payload.isCurrent) {
                  return (
                    <circle
                      key={`dot-${payload.x}`}
                      cx={cx}
                      cy={cy}
                      r={5}
                      stroke="var(--color-jade)"
                      strokeWidth={2}
                      fill="var(--color-background)"
                    />
                  );
                }
                return (
                  <circle
                    key={`dot-${payload.x}`}
                    cx={cx}
                    cy={cy}
                    r={2.5}
                    fill="var(--color-jade)"
                    stroke="none"
                  />
                );
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
