"use client";

export default function SecurityPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Security Analytics</h1>
      <p className="text-muted-foreground">
        Monitor prompt injection attempts, jailbreak attacks, and sensitive data
        detection events.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border p-4">
          <p className="text-sm text-muted-foreground">Injection Attempts</p>
          <p className="mt-1 text-2xl font-bold">0</p>
        </div>
        <div className="rounded-lg border border-border p-4">
          <p className="text-sm text-muted-foreground">Jailbreak Attempts</p>
          <p className="mt-1 text-2xl font-bold">0</p>
        </div>
        <div className="rounded-lg border border-border p-4">
          <p className="text-sm text-muted-foreground">PII Detected</p>
          <p className="mt-1 text-2xl font-bold">0</p>
        </div>
        <div className="rounded-lg border border-border p-4">
          <p className="text-sm text-muted-foreground">Requests Blocked</p>
          <p className="mt-1 text-2xl font-bold">0</p>
        </div>
      </div>

      <div className="rounded-lg border border-border p-6">
        <h3 className="text-lg font-semibold">Recent Security Events</h3>
        <p className="mt-4 text-sm text-muted-foreground">
          No security events recorded yet.
        </p>
      </div>
    </div>
  );
}
