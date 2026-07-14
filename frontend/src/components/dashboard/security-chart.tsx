"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const mockData = [
  { date: "Jan 1", requests: 1200, blocked: 23, threats: 8 },
  { date: "Jan 2", requests: 1450, blocked: 31, threats: 12 },
  { date: "Jan 3", requests: 1380, blocked: 18, threats: 5 },
  { date: "Jan 4", requests: 1600, blocked: 42, threats: 15 },
  { date: "Jan 5", requests: 1520, blocked: 28, threats: 9 },
  { date: "Jan 6", requests: 1750, blocked: 55, threats: 22 },
  { date: "Jan 7", requests: 1680, blocked: 38, threats: 14 },
  { date: "Jan 8", requests: 1900, blocked: 47, threats: 18 },
  { date: "Jan 9", requests: 2100, blocked: 62, threats: 25 },
  { date: "Jan 10", requests: 1950, blocked: 44, threats: 16 },
  { date: "Jan 11", requests: 2200, blocked: 58, threats: 21 },
  { date: "Jan 12", requests: 2050, blocked: 51, threats: 19 },
  { date: "Jan 13", requests: 2300, blocked: 67, threats: 28 },
  { date: "Jan 14", requests: 2150, blocked: 49, threats: 17 },
];

export function SecurityChart() {
  return (
    <Card className="col-span-1 lg:col-span-2">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Security Events Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={mockData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(221, 83%, 53%)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(221, 83%, 53%)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorBlocked" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(0, 84%, 60%)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(0, 84%, 60%)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(38, 92%, 50%)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(38, 92%, 50%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis
                dataKey="date"
                className="text-xs"
                tick={{ fill: "hsl(215, 16%, 47%)", fontSize: 12 }}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: "hsl(215, 16%, 47%)", fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Area
                type="monotone"
                dataKey="requests"
                stroke="hsl(221, 83%, 53%)"
                fillOpacity={1}
                fill="url(#colorRequests)"
                name="Total Requests"
              />
              <Area
                type="monotone"
                dataKey="blocked"
                stroke="hsl(0, 84%, 60%)"
                fillOpacity={1}
                fill="url(#colorBlocked)"
                name="Blocked"
              />
              <Area
                type="monotone"
                dataKey="threats"
                stroke="hsl(38, 92%, 50%)"
                fillOpacity={1}
                fill="url(#colorThreats)"
                name="Threats Detected"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
