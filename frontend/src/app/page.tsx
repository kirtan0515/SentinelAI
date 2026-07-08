import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navigation */}
      <nav className="border-b border-border">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">S</span>
            </div>
            <span className="text-xl font-bold">SentinelAI</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-24 text-center">
        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
          Enterprise AI
          <span className="text-primary"> Security Gateway</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
          Protect your LLM applications from prompt injection, jailbreak attacks,
          data leakage, and unauthorized access. Monitor, authenticate, and audit
          every AI interaction.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            href="/register"
            className="rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition"
          >
            Start Free Trial
          </Link>
          <Link
            href="/docs"
            className="rounded-md border border-border px-6 py-3 text-sm font-medium hover:bg-accent transition"
          >
            View Documentation
          </Link>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-center text-3xl font-bold">Core Security Features</h2>
        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="rounded-lg border border-border p-6 hover:border-primary/50 transition"
            >
              <div className="mb-4 text-2xl">{feature.icon}</div>
              <h3 className="text-lg font-semibold">{feature.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          &copy; 2024 SentinelAI. Enterprise AI Security Gateway.
        </div>
      </footer>
    </div>
  );
}

const features = [
  {
    icon: "🛡️",
    title: "Prompt Injection Detection",
    description:
      "Detect and block malicious prompt injection attempts before they reach your LLMs.",
  },
  {
    icon: "🔒",
    title: "Jailbreak Prevention",
    description:
      "Identify and reject jailbreak attack patterns with real-time analysis.",
  },
  {
    icon: "🔐",
    title: "Sensitive Data Masking",
    description:
      "Automatically detect and mask PII, API keys, and credentials in prompts.",
  },
  {
    icon: "🤖",
    title: "Multi-Model Gateway",
    description:
      "Route requests to GPT, Claude, Gemini, or Llama with unified security controls.",
  },
  {
    icon: "📊",
    title: "Security Monitoring",
    description:
      "Real-time dashboards showing attack attempts, blocked requests, and system health.",
  },
  {
    icon: "📄",
    title: "Secure RAG",
    description:
      "Upload documents and query them securely with access-controlled embeddings.",
  },
];
