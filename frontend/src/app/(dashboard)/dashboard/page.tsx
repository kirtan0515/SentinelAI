"use client";

import { Activity, ShieldAlert, Cpu, Timer, TrendingUp, Zap } from "lucide-react";
import { StatsCard } from "@/components/dashboard/stats-card";
import { SecurityChart } from "@/components/dashboard/security-chart";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const modelUsage = [
  { name: "GPT-4", requests: 4523, percentage: 42, color: "bg-blue-500" },
  { name: "Claude 3 Sonnet", requests: 2871, percentage: 27, color: "bg-purple-500" },
  { name: "GPT-3.5 Turbo", requests: 1854, percentage: 17, color: "bg-green-500" },
  { name: "Gemini Pro", requests: 956, percentage: 9, color: "bg-yellow-500" },
  { name: "Llama 2 (Local)", requests: 534, percentage: 5, color: "bg-orange-500" },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="mt-1 text-muted-foreground">
          Monitor your AI security posture in real time.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Requests"
          value="10,738"
          change="+12.5% from last week"
          changeType="positive"
          icon={Activity}
        />
        <StatsCard
          title="Blocked Attacks"
          value="284"
          change="+5.2% from last week"
          changeType="negative"
          icon={ShieldAlert}
          iconColor="text-red-500"
        />
        <StatsCard
          title="Active Models"
          value="5"
          change="All healthy"
          changeType="positive"
          icon={Cpu}
          iconColor="text-purple-500"
        />
        <StatsCard
          title="Avg Latency"
          value="142ms"
          change="-8ms from last week"
          changeType="positive"
          icon={Timer}
          iconColor="text-green-500"
        />
      </div>

      {/* Security Events Chart */}
      <div className="grid gap-4 lg:grid-cols-3">
        <SecurityChart />
        {/* Model Usage Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Model Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {modelUsage.map((model) => (
                <div key={model.name} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{model.name}</span>
                    <span className="text-muted-foreground">
                      {model.requests.toLocaleString()}
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-secondary">
                    <div
                      className={`h-2 rounded-full ${model.color}`}
                      style={{ width: `${model.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-2 rounded-md bg-muted/50 p-3">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-xs text-muted-foreground">
                Total: 10,738 requests this week
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity & Quick Stats */}
      <div className="grid gap-4 lg:grid-cols-2">
        <RecentActivity />
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <StatusRow label="API Gateway" status="operational" />
              <StatusRow label="Security Engine" status="operational" />
              <StatusRow label="RAG Pipeline" status="operational" />
              <StatusRow label="Vector Store" status="operational" />
              <StatusRow label="Rate Limiter" status="operational" />
              <StatusRow label="Guardrails (NeMo)" status="degraded" />
            </div>
            <div className="mt-4 flex items-center gap-2 rounded-md bg-yellow-500/10 p-3">
              <Zap className="h-4 w-4 text-yellow-600" />
              <span className="text-xs text-yellow-700 dark:text-yellow-400">
                NeMo Guardrails experiencing higher latency than normal
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatusRow({ label, status }: { label: string; status: "operational" | "degraded" | "down" }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm">{label}</span>
      <Badge variant={status === "operational" ? "success" : status === "degraded" ? "warning" : "danger"}>
        {status}
      </Badge>
    </div>
  );
}
