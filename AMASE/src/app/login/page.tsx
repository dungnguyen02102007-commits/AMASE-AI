"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/utils/supabase/client";

type Mode = "signin" | "signup";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") ?? "/dashboard";

  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setInfo(null);

    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }
    if (mode === "signup" && password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setSubmitting(true);
    const supabase = createClient();

    try {
      if (mode === "signin") {
        const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
        if (signInError) {
          setError(signInError.message);
          setSubmitting(false);
          return;
        }
        router.push(nextPath);
        router.refresh();
      } else {
        const { data, error: signUpError } = await supabase.auth.signUp({ email, password });
        if (signUpError) {
          setError(signUpError.message);
          setSubmitting(false);
          return;
        }
        if (!data.session) {
          setInfo("Check your email to confirm your account, then sign in.");
          setMode("signin");
          setSubmitting(false);
          return;
        }
        router.push(nextPath);
        router.refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setSubmitting(false);
    }
  }

  function toggleMode() {
    setMode((m) => (m === "signin" ? "signup" : "signin"));
    setError(null);
    setInfo(null);
  }

  const inputCls = "w-full text-[13px] bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-colors";

  return (
    <div className="w-full max-w-[400px]">
      <div className="text-center mb-8">
        <p className="text-[11px] font-bold uppercase tracking-widest text-indigo-500 mb-2">
          {mode === "signin" ? "Sign in" : "Create account"}
        </p>
        <h1 className="text-[24px] font-extrabold tracking-tight text-slate-900">
          {mode === "signin" ? "Welcome back" : "Start analyzing resumes"}
        </h1>
        <p className="text-[13px] text-slate-500 mt-1.5">
          {mode === "signin" ? "Pick up where you left off." : "Free to start. No credit card required."}
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-black/[0.07] shadow-sm p-6">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label htmlFor="email" className="block text-[12px] font-semibold text-slate-700 mb-1.5">Email</label>
            <input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" className={inputCls} />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="password" className="block text-[12px] font-semibold text-slate-700">Password</label>
              {mode === "signin" && <a href="#" className="text-[11px] font-semibold text-indigo-600 hover:underline">Forgot?</a>}
            </div>
            <input id="password" type="password" autoComplete={mode === "signin" ? "current-password" : "new-password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder={mode === "signup" ? "At least 6 characters" : "********"} className={inputCls} />
          </div>

          {error && <p className="text-[12px] text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}
          {info && <p className="text-[12px] text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-2">{info}</p>}

          <button type="submit" disabled={submitting} className="mt-1 w-full py-2.5 rounded-xl bg-slate-900 hover:bg-black text-white text-[13px] font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
            {submitting && (
              <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            )}
            {submitting ? (mode === "signin" ? "Signing in..." : "Creating account...") : (mode === "signin" ? "Sign in" : "Create account")}
          </button>
        </form>
      </div>

      <p className="text-center text-[12px] text-slate-500 mt-6">
        {mode === "signin" ? "New to ResumeIQ?" : "Already have an account?"}{" "}
        <button type="button" onClick={toggleMode} className="font-semibold text-indigo-600 hover:underline">
          {mode === "signin" ? "Create an account" : "Sign in"}
        </button>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-slate-50/60 flex flex-col">
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
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <Suspense fallback={null}>
          <LoginForm />
        </Suspense>
      </main>
    </div>
  );
}
