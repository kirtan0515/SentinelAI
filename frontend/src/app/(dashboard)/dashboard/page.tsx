"use client";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <p className="text-muted-foreground">
        Welcome to SentinelAI. Monitor your AI security posture.
      </p>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Requests" value="0" change="+0%" />
        <StatCard title="Blocked Attacks" value="0" change="+0%" />
        <StatCard title="Active Users" value="1" change="" />
        <StatCard title="Avg Latency" value="0ms" change="" />
      </div>

      {/* Placeholder for charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">Request Volume</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Request volume chart will be displayed here.
          </p>
        </div>
        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">Security Events</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Security event timeline will be displayed here.
          </p>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  change,
}: {
  title: string;
  value: string;
  change: string;
}) {
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
      {change && (
        <p className="mt-1 text-xs text-muted-foreground">{change}</p>
      )}
    </div>
  );
}
