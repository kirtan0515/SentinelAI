"use client";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>
      <p className="text-muted-foreground">
        Manage your account settings and preferences.
      </p>

      <div className="space-y-6">
        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">Profile</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Update your name, email, and profile information.
          </p>
        </div>

        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">Security</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Change password, enable MFA, manage sessions.
          </p>
        </div>

        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">API Keys</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Manage your personal AI provider API keys.
          </p>
        </div>

        <div className="rounded-lg border border-border p-6">
          <h3 className="text-lg font-semibold">Preferences</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Default model, theme, notification settings.
          </p>
        </div>
      </div>
    </div>
  );
}
