"use client";

import {
  Shield,
  AlertTriangle,
  ShieldAlert,
  Eye,
  TrendingUp,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatsCard } from "@/components/dashboard/stats-card";
import { cn } from "@/lib/utils";

// Mock data
const threatDistribution = [
  { name: "Prompt Injection", value: 124, color: "#ef4444" },
  { name: "Jailbreak Attempts", value: 87, color: "#f97316" },
  { name: "PII Exposure", value: 56, color: "#eab308" },
  { name: "Data Exfiltration", value: 17, color: "#8b5cf6" },
];

const timelineData = [
  { date: "Mon", injection: 18, jailbreak: 12, pii: 8 },
  { date: "Tue", injection: 22, jailbreak: 15, pii: 10 },
  { date: "Wed", injection: 15, jailbreak: 9, pii: 12 },
  { date: "Thu", injection: 28, jailbreak: 18, pii: 7 },
  { date: "Fri", injection: 20, jailbreak: 14, pii: 9 },
  { date: "Sat", injection: 12, jailbreak: 8, pii: 5 },
  { date: "Sun", injection: 9, jailbreak: 11, pii: 5 },
];

const severityBreakdown = [
  { level: "Critical", count: 12, color: "bg-red-500", percentage: 4 },
  { level: "High", count: 67, color: "bg-orange-500", percentage: 24 },
  { level: "Medium", count: 134, color: "bg-yellow-500", percentage: 47 },
  { level: "Low", count: 71, color: "bg-blue-500", percentage: 25 },
];

const topPatterns = [
  { pattern: "DAN (Do Anything Now)", attempts: 34, successRate: "0%", category: "Jailbreak" },
  { pattern: "Ignore previous instructions", attempts: 28, successRate: "0%", category: "Injection" },
  { pattern: "Repeat the system prompt", attempts: 22, successRate: "0%", category: "Injection" },
  { pattern: "Encode as base64", attempts: 18, successRate: "0%", category: "Exfiltration" },
  { pattern: "Pretend you are...", attempts: 15, successRate: "0%", category: "Jailbreak" },
  { pattern: "SSN/Credit card in output", attempts: 12, successRate: "0%", category: "PII" },
];

const recentEvents = [
  { id: "1", type: "injection", severity: "critical", message: "Multi-step injection chain detected", user: "user_42", time: "3 min ago", model: "GPT-4" },
  { id: "2", type: "jailbreak", severity: "high", message: "DAN variant attempt blocked", user: "john.doe", time: "8 min ago", model: "Claude 3" },
  { id: "3", type: "pii", severity: "medium", message: "SSN pattern detected in output, redacted", user: "jane.smith", time: "15 min ago", model: "GPT-4" },
  { id: "4", type: "injection", severity: "high", message: "System prompt extraction attempt", user: "external_api", time: "22 min ago", model: "GPT-3.5" },
  { id: "5", type: "jailbreak", severity: "medium", message: "Role-play escalation detected", user: "bob.wilson", time: "35 min ago", model: "Gemini Pro" },
];

export default function SecurityPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Security Analytics</h1>
        <p className="mt-1 text-muted-foreground">
          Monitor prompt injection, jailbreak attacks, and sensitive data detection events.
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Injection Attempts"
          value="124"
          change="+18% this week"
          changeType="negative"
          icon={ShieldAlert}
          iconColor="text-red-500"
        />
        <StatsCard
          title="Jailbreak Attempts"
          value="87"
          change="+7% this week"
          changeType="negative"
          icon={AlertTriangle}
          iconColor="text-orange-500"
        />
        <StatsCard
          title="PII Detected"
          value="56"
          change="-12% this week"
          changeType="positive"
          icon={Eye}
          iconColor="text-yellow-500"
        />
        <StatsCard
          title="Block Rate"
          value="100%"
          change="All threats blocked"
          changeType="positive"
          icon={Shield}
          iconColor="text-green-500"
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Threat Distribution Pie */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Threat Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={threatDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    dataKey="value"
                    paddingAngle={4}
                  >
                    {threatDistribution.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: "12px" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Timeline */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Threat Timeline (This Week)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timelineData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="date" tick={{ fill: "hsl(215, 16%, 47%)", fontSize: 12 }} />
                  <YAxis tick={{ fill: "hsl(215, 16%, 47%)", fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                  <Area type="monotone" dataKey="injection" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} name="Injection" />
                  <Area type="monotone" dataKey="jailbreak" stackId="1" stroke="#f97316" fill="#f97316" fillOpacity={0.3} name="Jailbreak" />
                  <Area type="monotone" dataKey="pii" stackId="1" stroke="#eab308" fill="#eab308" fillOpacity={0.3} name="PII" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Severity & Recent Events */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Severity Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Severity Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {severityBreakdown.map((item) => (
                <div key={item.level} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{item.level}</span>
                    <span className="text-muted-foreground">{item.count} events ({item.percentage}%)</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-secondary">
                    <div
                      className={cn("h-2 rounded-full", item.color)}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Security Events */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Recent Security Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentEvents.map((event) => (
                <div key={event.id} className="flex items-start gap-3 rounded-md border border-border p-3">
                  <ShieldAlert className={cn(
                    "h-4 w-4 mt-0.5 shrink-0",
                    event.severity === "critical" ? "text-red-500" :
                    event.severity === "high" ? "text-orange-500" :
                    "text-yellow-500"
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{event.message}</p>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{event.user}</span>
                      <span>·</span>
                      <span>{event.model}</span>
                      <span>·</span>
                      <span>{event.time}</span>
                    </div>
                  </div>
                  <Badge
                    variant={
                      event.severity === "critical" ? "danger" :
                      event.severity === "high" ? "warning" :
                      "secondary"
                    }
                    className="text-[10px] shrink-0"
                  >
                    {event.severity}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Attack Patterns Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Top Blocked Attack Patterns</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Pattern</th>
                  <th className="px-4 py-3 text-left font-medium">Category</th>
                  <th className="px-4 py-3 text-left font-medium">Attempts</th>
                  <th className="px-4 py-3 text-left font-medium">Success Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {topPatterns.map((pattern, i) => (
                  <tr key={i} className="hover:bg-accent/50 transition-colors">
                    <td className="px-4 py-3 font-medium">{pattern.pattern}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className="text-[10px]">
                        {pattern.category}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{pattern.attempts}</td>
                    <td className="px-4 py-3">
                      <Badge variant="success" className="text-[10px]">{pattern.successRate}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
