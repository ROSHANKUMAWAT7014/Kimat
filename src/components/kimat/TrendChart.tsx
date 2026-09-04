import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cityTrend, formatRate } from "@/lib/kimat/model";

export function TrendChart({ cityId }: { cityId: string }) {
  const data = cityTrend(cityId);
  const first = data[0]?.rate ?? 0;
  const last = data[data.length - 1]?.rate ?? 0;
  const change = first ? ((last - first) / first) * 100 : 0;

  return (
    <div>
      <div className="mb-3 flex items-baseline justify-between">
        <span className="label-eyebrow">12-month ₹/sq.ft trend</span>
        <span
          className={`font-mono text-xs ${change >= 0 ? "text-jade" : "text-clay"}`}
        >
          {change >= 0 ? "+" : ""}
          {change.toFixed(1)}% YoY
        </span>
      </div>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-accent)" stopOpacity={0.45} />
                <stop offset="100%" stopColor="var(--color-accent)" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              axisLine={false}
              tickLine={false}
              domain={["dataMin - 400", "dataMax + 400"]}
              tickFormatter={(v: number) => `${Math.round(v / 1000)}k`}
            />
            <Tooltip
              contentStyle={{
                background: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: 12,
                fontSize: 12,
                color: "var(--color-foreground)",
              }}
              formatter={(v: number) => [formatRate(v) + "/sq.ft", "Rate"]}
            />
            <Area
              type="monotone"
              dataKey="rate"
              stroke="var(--color-accent)"
              strokeWidth={2}
              fill="url(#trendFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
