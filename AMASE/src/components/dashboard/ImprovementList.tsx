"use client";

import { Improvement, ImpactLevel } from "@/types/resume";

interface ImprovementListProps {
  improvements: Improvement[];
  onImproveClick: () => void;
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

export function ImprovementList({ improvements, onImproveClick }: ImprovementListProps) {
  const highImpactCount = improvements.filter((i) => i.impact === "high").length;

  return (
    <div className="bg-white rounded-2xl border border-black/[0.07] shadow-sm p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-[14px] font-bold tracking-tight">Improvement Suggestions</h3>
          <p className="text-[12px] text-[#555] mt-0.5">
            {improvements.length} actions to reach 72+ score
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 px-3 py-1.5 rounded-full">
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="18 15 12 9 6 15" />
          </svg>
          +{highImpactCount * 10}–{highImpactCount * 14} pts possible
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {improvements.map((imp) => {
          const impact = impactConfig[imp.impact];
          const catColor = categoryColors[imp.category] ?? "bg-slate-50 text-slate-500";

          return (
            <div
              key={imp.id}
              className="group flex gap-3 p-4 rounded-xl border border-slate-100 hover:border-slate-200 hover:shadow-sm transition-all cursor-pointer"
            >
              <div className="w-6 h-6 rounded-md bg-slate-100 group-hover:bg-slate-800 transition-colors flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-[10px] font-bold text-slate-500 group-hover:text-white transition-colors">
                  {String(imp.rank).padStart(2, "0")}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${catColor}`}>
                    {imp.category}
                  </span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${impact.cls}`}>
                    {impact.label}
                  </span>
                  <span className="ml-auto text-[11px] font-bold text-emerald-600">{imp.pointsGain}</span>
                </div>
                <p className="text-[12px] text-slate-600 leading-relaxed">{imp.suggestion}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-5 pt-4 border-t border-slate-100 flex gap-2">
        <button
          onClick={onImproveClick}
          className="flex-1 py-2.5 rounded-xl bg-slate-900 hover:bg-black text-white text-[13px] font-semibold transition-colors"
        >
          Improve Resume
        </button>
        <button className="px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-[13px] font-semibold transition-colors">
          Export PDF
        </button>
      </div>
    </div>
  );
}