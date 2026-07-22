"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Shield } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/auth/login`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || "Invalid credentials");
      }

      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      router.push("/dashboard");
    } catch (err: any) {
      // If backend is not running, allow demo mode
      if (err.message === "Failed to fetch" || err.message.includes("NetworkError")) {
        // Demo mode — simulate login
        localStorage.setItem("access_token", "demo-token");
        localStorage.setItem("refresh_token", "demo-refresh");
        localStorage.setItem("demo_user", JSON.stringify({
          id: "demo-user-id",
          email: email || "admin@sentinelai.io",
          username: "admin",
          full_name: "Demo Admin",
          role: "admin",
          is_active: true,
          is_verified: true,
          mfa_enabled: false,
        }));
        router.push("/dashboard");
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = () => {
    localStorage.setItem("access_token", "demo-token");
    localStorage.setItem("refresh_token", "demo-refresh");
    localStorage.setItem("demo_user", JSON.stringify({
      id: "demo-user-id",
      email: "admin@sentinelai.io",
      username: "admin",
      full_name: "Demo Admin",
      role: "admin",
      is_active: true,
      is_verified: true,
      mfa_enabled: false,
    }));
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f] px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-violet-600">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white tracking-tight">SentinelAI</span>
          </Link>
          <p className="mt-3 text-sm text-zinc-500">Sign in to your security dashboard</p>
        </div>

        {/* Form */}
        <div className="rounded-xl border border-white/10 bg-white/[0.02] p-6">
          {error && (
            <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-zinc-300 mb-1.5">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@sentinelai.io"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-zinc-300 mb-1.5">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-white py-2.5 text-sm font-medium text-black hover:bg-zinc-200 disabled:opacity-50 transition"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <div className="mt-4 relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/5" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-[#0a0a0f] px-3 text-zinc-600">or</span>
            </div>
          </div>

          <button
            onClick={handleDemoLogin}
            className="mt-4 w-full rounded-lg border border-white/10 py-2.5 text-sm font-medium text-zinc-300 hover:bg-white/5 transition"
          >
            Continue with Demo Account
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-zinc-600">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-blue-400 hover:text-blue-300 transition">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
