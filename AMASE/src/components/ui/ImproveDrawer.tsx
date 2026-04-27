"use client";

import { useEffect } from "react";
import { Improvement, ImpactLevel } from "@/types/resume";

interface ImproveDrawerProps {
  open: boolean;
  onClose: () => void;
  improvements: Improvement[];
}

const impactConfig: Record<ImpactLevel, { label: string; cls: string }> = {
  high: { label: "High Impact", cls: "bg-emerald-50 text-emerald-700 border border-emerald-100" },
  medium: { label: "Medium", cls: "bg-sky-50 text-sky-700 border border-sky-100" },
  low: { label: "Nice to Have", cls: "bg-slate-50 text-slate-500 border border-slate-100" },
};

const categoryColors: Record<string, string> = {
  Quantification: "bg-violet-50 text-violet-700",
  Keywords: "bg-blue-50 text-blue-700",
  Structure: "bg-amber-50 text-amber-700",
  Summary: "bg-pink-50 text-pink-700",
  Achievements: "bg-emerald-50 text-emerald-700",
  Education: "bg-slate-50 text-slate-500",
};

export function ImproveDrawer({ open, onClose, improvements }: ImproveDrawerProps) {
  // Lock body scroll while open
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const top3 = improvements.slice(0, 3);

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-black/30 backdrop-blur-[2px] transition-opacity duration-300 ${open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
      />

      {/* Drawer panel */}
      <div
        className={`fixed right-0 top-0 bottom-0 z-50 w-full max-w-[420px] bg-white shadow-2xl flex flex-col transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] ${open ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
          <div>
            <h2 className="text-[15px] font-bold tracking-tight">Improve Resume</h2>
            <p className="text-[12px] text-slate-500 mt-0.5">Top actions ranked by score impact</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-slate-100 transition-colors text-slate-500"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Score potential banner */}
        <div className="mx-6 mt-5 p-4 rounded-xl bg-gradient-to-br from-indigo-50 to-violet-50 border border-indigo-100">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-indigo-600">Score Potential</p>
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-extrabold text-slate-700">38 → </span>
              <span className="text-[13px] font-extrabold text-emerald-600">72–80</span>
            </div>
          </div>
          <div className="h-2 bg-indigo-100 rounded-full overflow-hidden">
            <div className="h-full w-[76%] rounded-full bg-gradient-to-r from-indigo-500 to-violet-500" />
          </div>
          <p className="text-[11px] text-indigo-500 mt-2">Apply all 3 changes to unlock +34–42 points</p>
        </div>

        {/* Top 3 improvements */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-3">
          {top3.map((imp, idx) => {
            const impact = impactConfig[imp.impact];
            const catColor = categoryColors[imp.category] ?? "bg-slate-50 text-slate-500";

            return (
              <div
                key={imp.id}
                className="rounded-xl border border-slate-100 hover:border-slate-200 hover:shadow-sm transition-all p-4 group"
              >
                {/* Rank + badges */}
                <div className="flex items-center gap-2 mb-2.5">
                  <div className="w-6 h-6 rounded-md bg-slate-100 group-hover:bg-slate-800 transition-colors flex items-center justify-center">
                    <span className="text-[10px] font-bold text-slate-500 group-hover:text-white transition-colors">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${catColor}`}>
                    {imp.category}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${impact.cls}`}>
                    {impact.label}
                  </span>
                  <span className="ml-auto text-[11px] font-bold text-emerald-600">{imp.pointsGain} pts</span>
                </div>

                {/* Suggestion text */}
                <p className="text-[12.5px] text-slate-600 leading-relaxed">{imp.suggestion}</p>

                {/* Apply button */}
                <button className="mt-3 w-full py-2 rounded-lg text-[12px] font-semibold bg-slate-900 hover:bg-black text-white transition-colors">
                  Apply rewrite →
                </button>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50">
          <button className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white text-[13px] font-semibold transition-all shadow-sm hover:shadow-md">
            Apply All with AI ✦
          </button>
          <p className="text-[10px] text-center text-slate-400 mt-2">
            AI rewrites preserve your voice and formatting
          </p>
        </div>
      </div>
    </>
  );
}