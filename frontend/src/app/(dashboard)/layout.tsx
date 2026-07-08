import Link from "next/link";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card">
        <div className="flex h-16 items-center border-b border-border px-6">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xs">S</span>
            </div>
            <span className="font-bold">SentinelAI</span>
          </Link>
        </div>
        <nav className="p-4 space-y-1">
          <NavItem href="/dashboard" label="Dashboard" icon="📊" />
          <NavItem href="/chat" label="AI Chat" icon="💬" />
          <NavItem href="/documents" label="Documents" icon="📄" />
          <NavItem href="/security" label="Security" icon="🛡️" />
          <NavItem href="/audit" label="Audit Logs" icon="📋" />
          <NavItem href="/admin" label="Admin" icon="⚙️" />
          <NavItem href="/settings" label="Settings" icon="🔧" />
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1">
        <header className="flex h-16 items-center justify-between border-b border-border px-6">
          <div />
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">Admin</span>
            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
              <span className="text-xs font-medium">A</span>
            </div>
          </div>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}

function NavItem({
  href,
  label,
  icon,
}: {
  href: string;
  label: string;
  icon: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition"
    >
      <span>{icon}</span>
      <span>{label}</span>
    </Link>
  );
}
