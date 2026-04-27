"use client";

import { useEffect, useState } from "react";

interface ScoreCardProps {
  score: number;
  maxScore: number;
  candidateName: string;
  targetRole: string;
  analysisDate: string;
  percentile: number;
  issueCount: number;
  scorePotential: { low: number; high: number };
}

function getScoreConfig(score: number) {
  if (score < 50) return { color: "#dc2626", label: "Needs Work", badgeCls: "bg-red-50 text-red-600 border border-red-100" };
  if (score < 75) return { color: "#d97706", label: "Developing", badgeCls: "bg-amber-50 text-amber-600 border border-amber-100" };
  return { color: "#059669", label: "Excellent", badgeCls: "bg-emerald-50 text-emerald-700 border border-emerald-100" };
}

export function ScoreCard({ score, maxScore, candidateName, targetRole, analysisDate, percentile, issueCount, scorePotential }: ScoreCardProps) {
  const [animated, setAnimated] = useState(false);
  const circumference = 2 * Math.PI * 54;
  const pct = score / maxScore;
  const offset = circumference - pct * circumference;
  const cfg = getScoreConfig(score);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 120);
    return () => clearTimeout(t);
  }, [score]);

  return (
    <div className="bg-white rounded-2xl border border-black/[0.07] shadow-sm p-6">
      <div className="flex gap-6 items-stretch flex-wrap">
        <div className="flex flex-col items-center gap-2 flex-shrink-0">
          <div className="relative w-[140px] h-[140px]">
            <svg width="140" height="140" viewBox="0 0 140 140" style={{ transform: "rotate(-90deg)" }}>
              <circle cx="70" cy="70" r="54" fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="10" />
              <circle cx="70" cy="70" r="54" fill="none" stroke={cfg.color} strokeWidth="10" strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={animated ? offset : circumference}
                style={{ transition: "stroke-dashoffset 1.4s cubic-bezier(0.34,1.1,0.64,1)" }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-black leading-none tabular-nums" style={{ color: cfg.color }}>{score}</span>
              <span className="text-[11px] text-slate-400 font-medium mt-1">/ {maxScore}</span>
            </div>
          </div>
          <span className={"text-[11px] font-bold px-3 py-1 rounded-full " + cfg.badgeCls}>{cfg.label}</span>
        </div>
        <div className="w-px bg-black/[0.07] self-stretch flex-shrink-0" />
        <div className="flex-1 flex flex-col justify-between min-w-[200px]">
          <div>
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-[18px] font-extrabold tracking-tight">{candidateName}</p>
                <p className="text-[13px] text-slate-500">{targetRole} candidate</p>
              </div>
              <span className="text-[11px] text-slate-400 mt-0.5 flex-shrink-0">{analysisDate}</span>
            </div>
            <div className="mb-3">
              <div className="flex justify-between text-[12px] text-slate-500 mb-1.5">
                <span>Overall progress</span>
                <span className="font-semibold">{Math.round(pct * 100)}%</span>
              </div>
              <div className="h-2 bg-black/[0.05] rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-[1400ms] ease-[cubic-bezier(0.34,1.56,0.64,1)]"
                  style={{ width: animated ? (pct * 100) + "%" : "0%", background: cfg.color }} />
              </div>
            </div>
          </div>
          <div className="flex gap-2.5 flex-wrap">
            {[
              { val: percentile + "th", label: "Percentile" },
              { val: String(issueCount), label: "Issues", color: "#dc2626" },
              { val: "+" + (scorePotential.high - score), label: "Pts possible", color: "#059669" },
              { val: "A-", label: "Target grade", color: "#4f46e5" },
            ].map(({ val, label, color }) => (
              <div key={label} className="flex flex-col items-center px-3.5 py-2.5 rounded-xl bg-black/[0.025] border border-black/[0.06] min-w-[68px] gap-0.5">
                <span className="text-[20px] font-extrabold tracking-tight leading-none" style={color ? { color } : {}}>{val}</span>
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}