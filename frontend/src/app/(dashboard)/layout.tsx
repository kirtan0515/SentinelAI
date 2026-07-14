"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  MessageSquare,
  FileText,
  Shield,
  ClipboardList,
  Users,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Bell,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/security", label: "Security", icon: Shield },
  { href: "/audit", label: "Audit Logs", icon: ClipboardList },
  { href: "/admin", label: "Admin", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const { user, logout } = useAuthStore();

  return (
    <div className="flex min-h-screen">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r border-border bg-card transition-transform lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-border px-6">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <Shield className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-bold text-lg">SentinelAI</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden rounded-md p-1 hover:bg-accent"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-col h-[calc(100vh-4rem)] justify-between">
          <div className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* User section at bottom */}
          <div className="border-t border-border p-4">
            <div className="flex items-center gap-3 rounded-md px-3 py-2">
              <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                <span className="text-xs font-semibold text-primary">
                  {user?.full_name?.charAt(0) || user?.username?.charAt(0)?.toUpperCase() || "U"}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {user?.full_name || user?.username || "User"}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {user?.email || "user@example.com"}
                </p>
              </div>
            </div>
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 min-w-0">
        <header className="flex h-16 items-center justify-between border-b border-border px-4 lg:px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-2 hover:bg-accent lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="hidden lg:block" />

          <div className="flex items-center gap-3">
            {/* Notifications */}
            <button className="relative rounded-md p-2 hover:bg-accent transition-colors">
              <Bell className="h-5 w-5 text-muted-foreground" />
              <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500" />
            </button>

            {/* User dropdown */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 rounded-md px-3 py-1.5 hover:bg-accent transition-colors"
              >
                <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                  <span className="text-xs font-semibold text-primary">
                    {user?.full_name?.charAt(0) || user?.username?.charAt(0)?.toUpperCase() || "U"}
                  </span>
                </div>
                <div className="hidden sm:block text-left">
                  <p className="text-sm font-medium">
                    {user?.full_name || user?.username || "Admin"}
                  </p>
                  <p className="text-xs text-muted-foreground capitalize">
                    {user?.role || "admin"}
                  </p>
                </div>
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 rounded-md border border-border bg-card shadow-lg z-50">
                  <div className="p-1">
                    <Link
                      href="/settings"
                      onClick={() => setUserMenuOpen(false)}
                      className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent transition-colors"
                    >
                      <Settings className="h-4 w-4" />
                      Settings
                    </Link>
                    <button
                      onClick={() => {
                        setUserMenuOpen(false);
                        logout();
                      }}
                      className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-red-600 hover:bg-accent transition-colors"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>
        <div className="p-4 lg:p-6">{children}</div>
      </main>
    </div>
  );
}
