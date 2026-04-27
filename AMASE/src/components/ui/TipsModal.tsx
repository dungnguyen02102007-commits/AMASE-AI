"use client";

import { useEffect } from "react";
import { Feedback } from "@/types/resume";

interface TipsModalProps {
  open: boolean;
  onClose: () => void;
  feedback: Feedback;
}

const TIP_CATEGORIES = [
  {
    key: "action" as const,
    label: "Action Verbs",
    icon: "⚡",
    color: "text-indigo-600",
    bg: "bg-indigo-50",
    border: "border-indigo-100",
    tip: "Start every bullet with a past-tense action verb. Aim for verbs in the top-100 PM power verbs list (e.g. Spearheaded, Orchestrated, Architected, Accelerated).",
  },
  {
    key: "specifics" as const,
    label: "Metrics & Numbers",
    icon: "📊",
    color: "text-sky-600",
    bg: "bg-sky-50",
    border: "border-sky-100",
    tip: "Quantify at least 70% of your experience bullets. Include revenue ($), percentage improvements (%), team size (#), and time savings. If you don't have exact numbers, estimate conservatively.",
  },
  {
    key: "overusage" as const,
    label: "Keyword Optimisation",
    icon: "🔑",
    color: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-100",
    tip: 'Mirror exact keywords from the job description. ATS systems look for: "OKR", "go-to-market", "cross-functional", "roadmap", "stakeholder alignment". Use them naturally once or twice each.',
  },
  {
    key: "avoided" as const,
    label: "Avoid Clichés",
    icon: "🚫",
    color: "text-red-600",
    bg: "bg-red-50",
    border: "border-red-100",
    tip: 'Remove "results-driven", "passionate", "team player", "hardworking", and "detail-oriented". Every recruiter sees these daily. Replace with concrete evidence of these traits instead.',
  },
];

const GLOBAL_TIPS = [
  { title: "One page rule", detail: "For < 10 years of experience, keep it to one page. Ruthlessly cut old or irrelevant roles." },
  { title: "Reverse chronological", detail: "Always list experience newest-first. Recruiters read top-to-bottom." },
  { title: "Summary is your hook", detail: "Your 3-line summary must answer: what you do, for whom, and your biggest win. Tailor it per role." },
  { title: "ATS formatting", detail: "Avoid tables, text boxes, headers/footers, and images. Use plain sections with standard headings." },
];

export function TipsModal({ open, onClose, feedback }: TipsModalProps) {
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-black/30 backdrop-blur-[2px] transition-opacity duration-200 ${open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
      />

      {/* Modal */}
      <div
        className={`fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none`}
      >
        <div
          className={`relative w-full max-w-2xl max-h-[90vh] bg-white rounded-2xl shadow-2xl flex flex-col pointer-events-auto transition-all duration-300 ${open ? "opacity-100 scale-100 translate-y-0" : "opacity-0 scale-95 translate-y-4"}`}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 flex-shrink-0">
            <div>
              <h2 className="text-[15px] font-bold tracking-tight">Resume Tips</h2>
              <p className="text-[12px] text-slate-500 mt-0.5">
                {Object.values(feedback).flat().length} issues · Personalised to your resume
              </p>
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

          {/* Scrollable content */}
          <div className="overflow-y-auto flex-1 px-6 py-5 space-y-4">
            {/* Categorised tips */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {TIP_CATEGORIES.map((cat) => {
                const issueCount = feedback[cat.key].length;
                const urgentCount = feedback[cat.key].filter((i) => i.severity === "high").length;

                return (
                  <div
                    key={cat.key}
                    className={`rounded-xl border p-4 ${cat.bg} ${cat.border}`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{cat.icon}</span>
                      <span className={`text-[12px] font-bold ${cat.color}`}>{cat.label}</span>
                      {urgentCount > 0 && (
                        <span className="ml-auto text-[10px] font-bold bg-red-50 text-red-500 border border-red-100 px-1.5 py-0.5 rounded-full">
                          {urgentCount} urgent
                        </span>
                      )}
                    </div>
                    <p className="text-[11.5px] text-slate-600 leading-relaxed">{cat.tip}</p>

                    {/* Issues from this category */}
                    {issueCount > 0 && (
                      <div className="mt-3 pt-3 border-t border-white/60 space-y-1.5">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Your issues</p>
                        {feedback[cat.key].slice(0, 2).map((item) => (
                          <p key={item.id} className="text-[11px] text-slate-600 leading-snug">
                            <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 align-middle ${item.severity === "high" ? "bg-red-500" : item.severity === "medium" ? "bg-amber-400" : "bg-slate-300"}`} />
                            {item.text}
                          </p>
                        ))}
                        {issueCount > 2 && (
                          <p className="text-[10px] text-slate-400">+{issueCount - 2} more issues</p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Global tips */}
            <div>
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">General Best Practices</p>
              <div className="space-y-2">
                {GLOBAL_TIPS.map((tip) => (
                  <div key={tip.title} className="flex gap-3 p-3 rounded-xl border border-slate-100 hover:border-slate-200 transition-colors">
                    <div className="w-1.5 h-1.5 rounded-full bg-slate-300 mt-[5px] flex-shrink-0" />
                    <div>
                      <p className="text-[12px] font-semibold text-slate-700">{tip.title}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">{tip.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-slate-100 flex-shrink-0">
            <button
              onClick={onClose}
              className="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-black text-white text-[13px] font-semibold transition-colors"
            >
              Got it — back to analysis
            </button>
          </div>
        </div>
      </div>
    </>
  );
}