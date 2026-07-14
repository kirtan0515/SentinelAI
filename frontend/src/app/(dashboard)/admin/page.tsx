"use client";

import { useState } from "react";
import {
  Users,
  Cpu,
  Shield,
  Activity,
  MoreVertical,
  Check,
  X,
  Settings,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// Mock data
const mockUsers = [
  { id: "1", email: "john.doe@company.com", role: "admin", status: "active", lastLogin: "2024-01-16T14:30:00Z" },
  { id: "2", email: "jane.smith@company.com", role: "analyst", status: "active", lastLogin: "2024-01-16T12:15:00Z" },
  { id: "3", email: "bob.wilson@company.com", role: "user", status: "active", lastLogin: "2024-01-15T09:45:00Z" },
  { id: "4", email: "alice.chen@company.com", role: "analyst", status: "active", lastLogin: "2024-01-16T08:20:00Z" },
  { id: "5", email: "david.brown@company.com", role: "user", status: "inactive", lastLogin: "2024-01-10T16:00:00Z" },
  { id: "6", email: "sarah.jones@company.com", role: "user", status: "active", lastLogin: "2024-01-16T11:30:00Z" },
];

const mockModels = [
  { id: "1", name: "GPT-4", provider: "OpenAI", enabled: true, isDefault: true, maxTokens: 8192, temp: 0.7 },
  { id: "2", name: "GPT-3.5 Turbo", provider: "OpenAI", enabled: true, isDefault: false, maxTokens: 4096, temp: 0.7 },
  { id: "3", name: "Claude 3 Sonnet", provider: "Anthropic", enabled: true, isDefault: false, maxTokens: 4096, temp: 0.7 },
  { id: "4", name: "Gemini Pro", provider: "Google", enabled: true, isDefault: false, maxTokens: 8192, temp: 0.8 },
  { id: "5", name: "Llama 2", provider: "Ollama (Local)", enabled: false, isDefault: false, maxTokens: 4096, temp: 0.7 },
];

const guardrailsConfig = [
  { id: "1", name: "Prompt Injection Detection", enabled: true, threshold: 0.85, description: "Detects attempts to override system instructions" },
  { id: "2", name: "Jailbreak Prevention", enabled: true, threshold: 0.80, description: "Blocks known jailbreak patterns (DAN, etc.)" },
  { id: "3", name: "PII Detection & Redaction", enabled: true, threshold: 0.90, description: "Identifies and redacts personal information" },
  { id: "4", name: "Topic Guardrails", enabled: true, threshold: 0.75, description: "Restricts conversation to approved topics" },
  { id: "5", name: "Output Validation", enabled: false, threshold: 0.70, description: "Validates model output before delivery" },
];

const systemHealth = [
  { name: "API Gateway", status: "healthy", uptime: "99.99%", latency: "12ms" },
  { name: "Security Engine", status: "healthy", uptime: "99.98%", latency: "45ms" },
  { name: "PostgreSQL", status: "healthy", uptime: "99.99%", latency: "3ms" },
  { name: "Redis Cache", status: "healthy", uptime: "99.99%", latency: "1ms" },
  { name: "Vector Store (Qdrant)", status: "healthy", uptime: "99.95%", latency: "8ms" },
  { name: "NeMo Guardrails", status: "degraded", uptime: "99.2%", latency: "120ms" },
];

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<"users" | "models" | "guardrails" | "health">("users");

  const tabs = [
    { id: "users" as const, label: "Users", icon: Users },
    { id: "models" as const, label: "Models", icon: Cpu },
    { id: "guardrails" as const, label: "Guardrails", icon: Shield },
    { id: "health" as const, label: "System Health", icon: Activity },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Admin Portal</h1>
        <p className="mt-1 text-muted-foreground">
          Manage users, AI models, guardrails configuration, and system health.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors",
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTab === "users" && <UsersPanel />}
      {activeTab === "models" && <ModelsPanel />}
      {activeTab === "guardrails" && <GuardrailsPanel />}
      {activeTab === "health" && <HealthPanel />}
    </div>
  );
}

function UsersPanel() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold">User Management</CardTitle>
        <Button size="sm">Add User</Button>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Email</th>
                <th className="px-4 py-3 text-left font-medium">Role</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium">Last Login</th>
                <th className="px-4 py-3 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {mockUsers.map((user) => (
                <tr key={user.id} className="hover:bg-accent/50 transition-colors">
                  <td className="px-4 py-3 font-medium">{user.email}</td>
                  <td className="px-4 py-3">
                    <Badge variant={user.role === "admin" ? "default" : user.role === "analyst" ? "secondary" : "outline"} className="text-[10px]">
                      {user.role}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={user.status === "active" ? "success" : "secondary"} className="text-[10px]">
                      {user.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(user.lastLogin).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function ModelsPanel() {
  const [models, setModels] = useState(mockModels);

  const toggleModel = (id: string) => {
    setModels((prev) =>
      prev.map((m) => (m.id === id ? { ...m, enabled: !m.enabled } : m))
    );
  };

  const setDefault = (id: string) => {
    setModels((prev) =>
      prev.map((m) => ({ ...m, isDefault: m.id === id }))
    );
  };

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {models.map((model) => (
        <Card key={model.id} className={cn(!model.enabled && "opacity-60")}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">{model.name}</h3>
                <p className="text-xs text-muted-foreground">{model.provider}</p>
              </div>
              {model.isDefault && (
                <Badge variant="default" className="text-[10px]">Default</Badge>
              )}
            </div>
            <div className="mt-3 space-y-2 text-xs text-muted-foreground">
              <div className="flex justify-between">
                <span>Max Tokens</span>
                <span>{model.maxTokens.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Temperature</span>
                <span>{model.temp}</span>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2">
              <Button
                variant={model.enabled ? "outline" : "default"}
                size="sm"
                className="flex-1 text-xs"
                onClick={() => toggleModel(model.id)}
              >
                {model.enabled ? "Disable" : "Enable"}
              </Button>
              {!model.isDefault && model.enabled && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  onClick={() => setDefault(model.id)}
                >
                  Set Default
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function GuardrailsPanel() {
  const [rules, setRules] = useState(guardrailsConfig);

  const toggleRule = (id: string) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r))
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Guardrails Configuration</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className={cn(
                "flex items-center gap-4 rounded-md border border-border p-4 transition-opacity",
                !rule.enabled && "opacity-60"
              )}
            >
              <button
                onClick={() => toggleRule(rule.id)}
                className={cn(
                  "shrink-0 h-5 w-9 rounded-full transition-colors relative",
                  rule.enabled ? "bg-primary" : "bg-muted"
                )}
              >
                <span
                  className={cn(
                    "absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform",
                    rule.enabled ? "translate-x-4.5 left-0.5" : "translate-x-0.5 left-0"
                  )}
                />
              </button>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{rule.name}</p>
                  <Badge variant="outline" className="text-[10px]">
                    Threshold: {rule.threshold}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">{rule.description}</p>
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function HealthPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">System Health</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Service</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium">Uptime</th>
                <th className="px-4 py-3 text-left font-medium">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {systemHealth.map((service) => (
                <tr key={service.name} className="hover:bg-accent/50 transition-colors">
                  <td className="px-4 py-3 font-medium">{service.name}</td>
                  <td className="px-4 py-3">
                    <Badge
                      variant={service.status === "healthy" ? "success" : service.status === "degraded" ? "warning" : "danger"}
                      className="text-[10px]"
                    >
                      <span className={cn(
                        "mr-1.5 h-1.5 w-1.5 rounded-full inline-block",
                        service.status === "healthy" ? "bg-green-500" :
                        service.status === "degraded" ? "bg-yellow-500" : "bg-red-500"
                      )} />
                      {service.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{service.uptime}</td>
                  <td className="px-4 py-3 text-muted-foreground">{service.latency}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
