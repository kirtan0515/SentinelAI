"use client";

import { useState } from "react";
import {
  User,
  Lock,
  Key,
  Palette,
  Eye,
  EyeOff,
  Copy,
  Plus,
  Trash2,
  Save,
  Moon,
  Sun,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState<"profile" | "password" | "apikeys" | "preferences">("profile");

  const sections = [
    { id: "profile" as const, label: "Profile", icon: User },
    { id: "password" as const, label: "Password", icon: Lock },
    { id: "apikeys" as const, label: "API Keys", icon: Key },
    { id: "preferences" as const, label: "Preferences", icon: Palette },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="mt-1 text-muted-foreground">
          Manage your account settings and preferences.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        {/* Sidebar Navigation */}
        <nav className="space-y-1">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                  activeSection === section.id
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {section.label}
              </button>
            );
          })}
        </nav>

        {/* Content */}
        <div>
          {activeSection === "profile" && <ProfileSection />}
          {activeSection === "password" && <PasswordSection />}
          {activeSection === "apikeys" && <ApiKeysSection />}
          {activeSection === "preferences" && <PreferencesSection />}
        </div>
      </div>
    </div>
  );
}

function ProfileSection() {
  const [form, setForm] = useState({
    fullName: "John Doe",
    email: "john.doe@company.com",
    username: "johndoe",
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Profile Information</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="text-sm font-medium">Full Name</label>
            <input
              type="text"
              value={form.fullName}
              onChange={(e) => setForm({ ...form, fullName: e.target.value })}
              className="mt-1 w-full rounded-md border border-input bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="mt-1 w-full rounded-md border border-input bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Username</label>
            <input
              type="text"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="mt-1 w-full rounded-md border border-input bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <Button className="mt-2">
            <Save className="mr-2 h-4 w-4" />
            Save Changes
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function PasswordSection() {
  const [form, setForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Change Password</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="text-sm font-medium">Current Password</label>
            <input
              type="password"
              value={form.currentPassword}
              onChange={(e) => setForm({ ...form, currentPassword: e.target.value })}
              placeholder="Enter current password"
              className="mt-1 w-full rounded-md border border-input bg-background px-4 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="text-sm font-medium">New Password</label>
            <input
              type="password"
              value={form.newPassword}
              onChange={(e) => setForm({ ...form, newPassword: e.target.value })}
              placeholder="Enter new password"
              className="mt-1 w-full rounded-md border border-input bg-background px-4 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Confirm New Password</label>
            <input
              type="password"
              value={form.confirmPassword}
              onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
              placeholder="Confirm new password"
              className="mt-1 w-full rounded-md border border-input bg-background px-4 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <Button className="mt-2">
            <Lock className="mr-2 h-4 w-4" />
            Update Password
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function ApiKeysSection() {
  const [keys, setKeys] = useState([
    { id: "1", name: "OpenAI API Key", value: "sk-proj-****************************abcD", visible: false, createdAt: "2024-01-10" },
    { id: "2", name: "Anthropic API Key", value: "sk-ant-****************************efgH", visible: false, createdAt: "2024-01-12" },
    { id: "3", name: "Google AI Key", value: "AIza****************************ijkL", visible: false, createdAt: "2024-01-14" },
  ]);

  const toggleVisibility = (id: string) => {
    setKeys((prev) =>
      prev.map((k) => (k.id === id ? { ...k, visible: !k.visible } : k))
    );
  };

  const deleteKey = (id: string) => {
    setKeys((prev) => prev.filter((k) => k.id !== id));
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold">API Keys</CardTitle>
        <Button size="sm">
          <Plus className="mr-2 h-3 w-3" />
          Add Key
        </Button>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {keys.map((key) => (
            <div
              key={key.id}
              className="flex items-center gap-3 rounded-md border border-border p-3"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{key.name}</p>
                <p className="text-xs font-mono text-muted-foreground mt-0.5">
                  {key.visible ? key.value.replace(/\*/g, "x") : key.value}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Added {key.createdAt}
                </p>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => toggleVisibility(key.id)}
                >
                  {key.visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Copy className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-red-500"
                  onClick={() => deleteKey(key.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function PreferencesSection() {
  const [prefs, setPrefs] = useState({
    defaultModel: "gpt-4",
    theme: "system",
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Preferences</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6 max-w-md">
          <div>
            <label className="text-sm font-medium">Default AI Model</label>
            <select
              value={prefs.defaultModel}
              onChange={(e) => setPrefs({ ...prefs, defaultModel: e.target.value })}
              className="mt-1 w-full rounded-md border border-input bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              <option value="gemini-pro">Gemini Pro</option>
              <option value="llama2">Llama 2 (Local)</option>
            </select>
          </div>

          <div>
            <label className="text-sm font-medium">Theme</label>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {(["light", "dark", "system"] as const).map((theme) => (
                <button
                  key={theme}
                  onClick={() => setPrefs({ ...prefs, theme })}
                  className={cn(
                    "flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition-colors",
                    prefs.theme === theme
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border hover:bg-accent"
                  )}
                >
                  {theme === "light" && <Sun className="h-4 w-4" />}
                  {theme === "dark" && <Moon className="h-4 w-4" />}
                  {theme === "system" && <Palette className="h-4 w-4" />}
                  <span className="capitalize">{theme}</span>
                </button>
              ))}
            </div>
          </div>

          <Button>
            <Save className="mr-2 h-4 w-4" />
            Save Preferences
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
