"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }

    // Simulated auth — real backend wired later
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      router.push("/dashboard");
    }, 700);
  }

  return (
    <div className="min-h-screen bg-slate-50/60 flex flex-col">
      {/* ── Top bar ─────────────────────────────────────────────────── */}
      <header className="h-14 bg-white border-b border-black/[0.07] flex items-center px-5">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 bg-slate-900 rounded-lg flex items-center justify-center">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2 10L7 3L12 10H2Z" fill="white" opacity="0.9" />
              <circle cx="7" cy="10" r="2" fill="white" />
            </svg>
          </div>
          <span className="font-extrabold text-[15px] tracking-tight">ResumeIQ</span>
        </Link>
      </header>

      {/* ── Centred card ────────────────────────────────────────────── */}
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-[400px]">
          <div className="text-center mb-8">
            <p className="text-[11px] font-bold uppercase tracking-widest text-indigo-500 mb-2">
              Sign in
            </p>
            <h1 className="text-[24px] font-extrabold tracking-tight text-slate-900">
              Welcome back
            </h1>
            <p className="text-[13px] text-slate-500 mt-1.5">
              Pick up where you left off.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-black/[0.07] shadow-sm p-6">
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-[12px] font-semibold text-slate-700 mb-1.5">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full text-[13px] bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-colors"
                />
              </div>

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label htmlFor="password" className="block text-[12px] font-semibold text-slate-700">
                    Password
                  </label>
                  <a href="#" className="text-[11px] font-semibold text-indigo-600 hover:underline">
                    Forgot?
                  </a>
                </div>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full text-[13px] bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-colors"
                />
              </div>

              {/* Error */}
              {error && (
                <p className="text-[12px] text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                  {error}
                </p>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={submitting}
                className="mt-1 w-full py-2.5 rounded-xl bg-slate-900 hover:bg-black text-white text-[13px] font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {submitting && (
                  <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                )}
                {submitting ? "Signing in…" : "Sign in"}
              </button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-3 my-5">
              <div className="flex-1 h-px bg-slate-100" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">or</span>
              <div className="flex-1 h-px bg-slate-100" />
            </div>

            {/* SSO placeholder */}
            <button
              type="button"
              className="w-full py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-[13px] font-semibold transition-colors flex items-center justify-center gap-2"
            >
              <svg width="14" height="14" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.76h3.56c2.08-1.92 3.28-4.74 3.28-8.09Z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.56-2.76c-.98.66-2.24 1.06-3.72 1.06-2.86 0-5.29-1.93-6.15-4.53H2.17v2.84A11 11 0 0 0 12 23Z" />
                <path fill="#FBBC05" d="M5.85 14.11A6.6 6.6 0 0 1 5.5 12c0-.73.13-1.45.35-2.11V7.05H2.17A11 11 0 0 0 1 12c0 1.78.42 3.46 1.17 4.95l3.68-2.84Z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 0 0 2.17 7.05L5.85 9.9C6.71 7.31 9.14 5.38 12 5.38Z" />
              </svg>
              Continue with Google
            </button>
          </div>

          {/* Sign up link */}
          <p className="text-center text-[12px] text-slate-500 mt-6">
            New to ResumeIQ?{" "}
            <a href="#" className="font-semibold text-indigo-600 hover:underline">
              Create an account
            </a>
          </p>
        </div>
      </main>
    </div>
  );
}
