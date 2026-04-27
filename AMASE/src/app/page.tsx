import Link from "next/link";

const FEATURES = [
  {
    title: "AI-powered scoring",
    detail: "Get a 0–100 score across Impact, Presentation, and Competencies — calibrated against thousands of hires.",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
    accent: "bg-indigo-50 text-indigo-600 border-indigo-100",
  },
  {
    title: "Inline highlights",
    detail: "Click any feedback item and we scroll your CV to the exact line — flagged in amber, selected in indigo.",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 17l6-6 4 4 8-8" />
        <polyline points="14 7 21 7 21 14" />
      </svg>
    ),
    accent: "bg-violet-50 text-violet-600 border-violet-100",
  },
  {
    title: "Ranked improvements",
    detail: "Top suggestions are ranked by point gain, so you know which fix unlocks the biggest jump in score.",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
    ),
    accent: "bg-emerald-50 text-emerald-700 border-emerald-100",
  },
];

const STATS = [
  { value: "120k+", label: "Resumes analyzed" },
  { value: "4.8/5", label: "User rating" },
  { value: "+34", label: "Avg. score gain" },
];

export default function LandingPage() {
  return (
    <>
      {/* ── Navbar ───────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 h-14 bg-white/90 backdrop-blur border-b border-black/[0.07] flex items-center px-5 gap-3">
        <div className="flex items-center gap-2 flex-shrink-0">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-7 h-7 bg-slate-900 rounded-lg flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 10L7 3L12 10H2Z" fill="white" opacity="0.9" />
                <circle cx="7" cy="10" r="2" fill="white" />
              </svg>
            </div>
            <span className="font-extrabold text-[15px] tracking-tight">ResumeIQ</span>
          </Link>
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-2 flex-shrink-0">
          <Link
            href="/login"
            className="text-[12px] font-semibold text-slate-600 hover:text-slate-900 px-3 py-1.5 transition-colors"
          >
            Sign in
          </Link>
          <Link
            href="/dashboard"
            className="text-[12px] font-semibold text-white bg-slate-900 hover:bg-black rounded-lg px-3 py-1.5 transition-colors"
          >
            Try the demo
          </Link>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="max-w-[1100px] mx-auto px-6 pt-20 pb-16 text-center">
        <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-indigo-600 bg-indigo-50 border border-indigo-100 rounded-full px-3 py-1 mb-6">
          AI Resume Analysis
        </span>
        <h1 className="text-[44px] sm:text-[56px] font-black tracking-tight text-slate-900 leading-[1.05] max-w-3xl mx-auto">
          Know exactly why your resume isn&apos;t landing interviews.
        </h1>
        <p className="text-[16px] sm:text-[17px] text-slate-500 mt-6 max-w-xl mx-auto leading-relaxed">
          Upload a PDF. Get an instant score, line-by-line feedback, and ranked improvements that actually move the needle.
        </p>

        <div className="flex items-center justify-center gap-3 mt-10 flex-wrap">
          <Link
            href="/dashboard"
            className="text-[14px] font-semibold text-white bg-slate-900 hover:bg-black rounded-xl px-5 py-3 transition-colors shadow-sm"
          >
            Analyze my resume →
          </Link>
          <Link
            href="/login"
            className="text-[14px] font-semibold text-slate-700 border border-slate-200 hover:bg-slate-50 rounded-xl px-5 py-3 transition-colors"
          >
            Sign in
          </Link>
        </div>

        <p className="text-[12px] text-slate-400 mt-4">
          No credit card · Results in under 30 seconds
        </p>
      </section>

      {/* ── Stats strip ──────────────────────────────────────────────── */}
      <section className="max-w-[1100px] mx-auto px-6 pb-20">
        <div className="grid grid-cols-3 gap-4 sm:gap-6 max-w-2xl mx-auto">
          {STATS.map((stat) => (
            <div
              key={stat.label}
              className="text-center p-5 rounded-2xl bg-white border border-black/[0.06] shadow-sm"
            >
              <p className="text-[24px] sm:text-[28px] font-black tracking-tight text-slate-900 leading-none">
                {stat.value}
              </p>
              <p className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider mt-2">
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────────── */}
      <section className="max-w-[1100px] mx-auto px-6 pb-24">
        <div className="text-center mb-12">
          <p className="text-[11px] font-bold uppercase tracking-widest text-indigo-500 mb-2">
            Why ResumeIQ
          </p>
          <h2 className="text-[28px] sm:text-[32px] font-extrabold tracking-tight text-slate-900">
            Feedback that points to the line.
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="bg-white rounded-2xl border border-black/[0.07] shadow-sm p-6 hover:shadow-md transition-shadow"
            >
              <div className={"w-10 h-10 rounded-xl flex items-center justify-center border " + feature.accent}>
                {feature.icon}
              </div>
              <h3 className="text-[15px] font-bold text-slate-900 mt-4">{feature.title}</h3>
              <p className="text-[13px] text-slate-500 mt-1.5 leading-relaxed">{feature.detail}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────── */}
      <section className="max-w-[1100px] mx-auto px-6 pb-24">
        <div className="rounded-3xl bg-gradient-to-br from-slate-900 to-slate-800 p-10 sm:p-14 text-center">
          <h2 className="text-[24px] sm:text-[28px] font-extrabold tracking-tight text-white">
            Ready to see your score?
          </h2>
          <p className="text-[14px] text-slate-300 mt-3 max-w-md mx-auto">
            Drop in your PDF and get a full breakdown in seconds.
          </p>
          <Link
            href="/dashboard"
            className="inline-block text-[14px] font-semibold text-slate-900 bg-white hover:bg-slate-100 rounded-xl px-5 py-3 mt-7 transition-colors"
          >
            Analyze my resume →
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-100">
        <div className="max-w-[1100px] mx-auto px-6 py-6 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-slate-900 rounded-md flex items-center justify-center">
              <svg width="10" height="10" viewBox="0 0 14 14" fill="none">
                <path d="M2 10L7 3L12 10H2Z" fill="white" opacity="0.9" />
                <circle cx="7" cy="10" r="2" fill="white" />
              </svg>
            </div>
            <span className="text-[12px] font-bold text-slate-700">ResumeIQ</span>
            <span className="text-[11px] text-slate-400">© 2026</span>
          </div>
          <div className="flex items-center gap-5 text-[12px] text-slate-500">
            <a href="#" className="hover:text-slate-800 transition-colors">Privacy</a>
            <a href="#" className="hover:text-slate-800 transition-colors">Terms</a>
            <a href="#" className="hover:text-slate-800 transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </>
  );
}
