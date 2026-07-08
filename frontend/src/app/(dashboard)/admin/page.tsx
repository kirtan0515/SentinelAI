"use client";

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Admin Portal</h1>
      <p className="text-muted-foreground">
        Manage users, roles, AI models, and system configuration.
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">User Management</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            View, create, and manage user accounts and role assignments.
          </p>
        </div>

        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">Model Configuration</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Configure AI model providers, defaults, and rate limits.
          </p>
        </div>

        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">Guardrails Settings</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Configure NVIDIA NeMo Guardrails rules and thresholds.
          </p>
        </div>

        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">System Health</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Monitor system resources, uptime, and service status.
          </p>
        </div>
      </div>
    </div>
  );
}
