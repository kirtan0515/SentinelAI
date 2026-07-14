"use client";

import { Shield, AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ActivityItem {
  id: string;
  type: "allowed" | "blocked" | "flagged" | "info";
  message: string;
  timestamp: string;
  user: string;
  model?: string;
}

const mockActivity: ActivityItem[] = [
  {
    id: "1",
    type: "blocked",
    message: "Prompt injection attempt detected and blocked",
    timestamp: "2 min ago",
    user: "john.doe@company.com",
    model: "GPT-4",
  },
  {
    id: "2",
    type: "allowed",
    message: "Code generation request processed successfully",
    timestamp: "5 min ago",
    user: "jane.smith@company.com",
    model: "Claude 3 Sonnet",
  },
  {
    id: "3",
    type: "flagged",
    message: "PII detected in output, redacted before delivery",
    timestamp: "12 min ago",
    user: "bob.wilson@company.com",
    model: "GPT-4",
  },
  {
    id: "4",
    type: "allowed",
    message: "RAG query with 3 document chunks retrieved",
    timestamp: "18 min ago",
    user: "alice.chen@company.com",
    model: "GPT-3.5 Turbo",
  },
  {
    id: "5",
    type: "blocked",
    message: "Jailbreak attempt blocked - DAN pattern detected",
    timestamp: "24 min ago",
    user: "external_user_42",
    model: "GPT-4",
  },
  {
    id: "6",
    type: "info",
    message: "New document uploaded and indexed (quarterly_report.pdf)",
    timestamp: "31 min ago",
    user: "jane.smith@company.com",
  },
];

const typeConfig = {
  allowed: { icon: CheckCircle, color: "text-green-600 dark:text-green-400", badge: "success" as const },
  blocked: { icon: XCircle, color: "text-red-600 dark:text-red-400", badge: "danger" as const },
  flagged: { icon: AlertTriangle, color: "text-yellow-600 dark:text-yellow-400", badge: "warning" as const },
  info: { icon: Shield, color: "text-blue-600 dark:text-blue-400", badge: "default" as const },
};

export function RecentActivity() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockActivity.map((item) => {
            const config = typeConfig[item.type];
            const Icon = config.icon;
            return (
              <div key={item.id} className="flex items-start gap-3">
                <Icon className={cn("h-4 w-4 mt-0.5 shrink-0", config.color)} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-tight">{item.message}</p>
                  <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{item.user}</span>
                    {item.model && (
                      <>
                        <span>·</span>
                        <span>{item.model}</span>
                      </>
                    )}
                    <span>·</span>
                    <span>{item.timestamp}</span>
                  </div>
                </div>
                <Badge variant={config.badge} className="shrink-0 text-[10px]">
                  {item.type}
                </Badge>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
