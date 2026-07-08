"use client";

export default function AuditPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Audit Logs</h1>
      <p className="text-muted-foreground">
        Complete history of all AI gateway requests with security analysis.
      </p>

      <div className="rounded-lg border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Timestamp</th>
              <th className="px-4 py-3 text-left font-medium">User</th>
              <th className="px-4 py-3 text-left font-medium">Model</th>
              <th className="px-4 py-3 text-left font-medium">Latency</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="px-4 py-3 text-left font-medium">Threat</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                No audit logs recorded yet.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
