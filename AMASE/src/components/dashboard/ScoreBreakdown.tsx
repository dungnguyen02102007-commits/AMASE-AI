"use client";

import { useEffect, useState } from "react";
import { ScoreBreakdown as ScoreBreakdownType } from "@/types/resume";

interface ScoreBreakdownProps {
  breakdown: ScoreBreakdownType;
}

interface BreakdownItem {
  key: keyof ScoreBreakdownType;
  label: string;
  description: string;
  max: number;
  color: string;
  bgColor: string;
  icon: string;
}

const items: BreakdownItem[] = [
  {
    key: "impact",
    label: "Impact",
    description: "Quantified achievements & results",
    max: 50,
    color: "#6366f1",
    bgColor: "#eef2ff",
    icon: "⚡",
  },
  {
    key: "presentation",
    label: "Presentation",
    description: "Formatting, structure & clarity",
    max: 30,
    color: "#0ea5e9",
    bgColor: "#f0f9ff",
    icon: "✦",
  },
  {
    key: "competencies",
    label: "Competencies",
    description: "Skills & keyword alignment",
    max: 20,
    color: "#10b981",
    bgColor: "#ecfdf5",
    icon: "◈",
  },
];

function BreakdownBar({
  item,
  value,
}: {
  item: BreakdownItem;
  value: number;
}) {
  const [animatedWidth, setAnimatedWidth] = useState(0);
  const percentage = (value / item.max) * 100;

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedWidth(percentage);
    }, 200);
    return () => clearTimeout(timer);
  }, [percentage]);

  return (
    <div className="flex items-center gap-4 p-4 rounded-xl border border-slate-100 hover:border-slate-200 transition-colors">
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0"
        style={{ backgroundColor: item.bgColor }}
      >
        {item.icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1.5">
          <div>
            <span className="text-sm font-semibold text-slate-700">
              {item.label}
            </span>
            <span className="text-xs text-slate-400 ml-2">
              {item.description}
            </span>
          </div>
          <div className="text-right flex-shrink-0 ml-2">
            <span
              className="text-sm font-bold"
              style={{ color: item.color }}
            >
              {value}
            </span>
            <span className="text-xs text-slate-400">/{item.max}</span>
          </div>
        </div>
        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{
              width: `${animatedWidth}%`,
              backgroundColor: item.color,
              transition: "width 1s cubic-bezier(0.34, 1.56, 0.64, 1)",
            }}
          />
        </div>
      </div>
    </div>
  );
}

export function ScoreBreakdown({ breakdown }: ScoreBreakdownProps) {
  const total = breakdown.impact + breakdown.presentation + breakdown.competencies;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400">
            Score Breakdown
          </h3>
          <p className="text-sm text-slate-600 mt-0.5">
            Points earned across 3 dimensions
          </p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-black text-slate-800">{total}</span>
          <span className="text-sm text-slate-400">/100</span>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <BreakdownBar
            key={item.key}
            item={item}
            value={breakdown[item.key]}
          />
        ))}
      </div>

      <div className="mt-5 pt-4 border-t border-slate-50 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-amber-400" />
        <p className="text-xs text-slate-500">
          Your score is in the{" "}
          <span className="font-semibold text-slate-700">bottom 15%</span> of
          candidates for this role.{" "}
          <button className="text-indigo-600 font-semibold hover:underline">
            See top performers →
          </button>
        </p>
      </div>
    </div>
  );
}
