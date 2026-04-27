"use client";

import { useState } from "react";
import { Feedback, FeedbackItem, Severity } from "@/types/resume";

interface FeedbackSidebarProps {
  feedback: Feedback;
  activeFeedbackId: string | null;
  onFeedbackClick: (id: string) => void;
}

const severityConfig: Record<Severity, { label: string; cls: string; dotCls: string }> = {
  high: { label: "High", cls: "bg-red-50 text-red-600 border border-red-100", dotCls: "bg-red-500" },
  medium: { label: "Med", cls: "bg-amber-50 text-amber-600 border border-amber-100", dotCls: "bg-amber-500" },
  low: { label: "Low", cls: "bg-slate-50 text-slate-500 border border-slate-100", dotCls: "bg-slate-400" },
};

const sections = [
  { key: "action" as const, label: "Action Oriented", desc: "Verb strength & active voice", countColor: "text-indigo-600", bg: "bg-indigo-50", urgentLabel: "2 urgent", defaultOpen: true },
  { key: "specifics" as const, label: "Specifics", desc: "Metrics & quantification", countColor: "text-cyan-600", bg: "bg-cyan-50", urgentLabel: "1 urgent" },
  { key: "overusage" as const, label: "Overusage", desc: "Repeated words & phrases", countColor: "text-amber-600", bg: "bg-amber-50", urgentLabel: "1 urgent" },
  { key: "avoided" as const, label: "Avoided Words", desc: "Clichés & weak language", countColor: "text-red-500", bg: "bg-red-50" },
];

function FeedbackItemRow({
  item, isActive, onClick,
}: {
  item: FeedbackItem;
  isActive: boolean;
  onClick: () => void;
}) {
  const sev = severityConfig[item.severity];

  return (
    <div
      onClick={onClick}
      className={`flex gap-3 p-3 rounded-xl cursor-pointer transition-all duration-150 relative ${
        isActive
          ? "bg-indigo-50/60 border border-indigo-200/60"
          : "border border-transparent hover:bg-black/[0.025] hover:border-black/[0.07]"
      }`}
    >
      {isActive && (
        <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-indigo-500 rounded-r" />
      )}
      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-[5px] ${sev.dotCls} ${item.severity === "high" ? "animate-pulse" : ""}`} />
      <div className="flex-1 min-w-0">
        <p className="text-[12px] font-semibold text-[#1a1a1a] leading-snug">{item.text}</p>
        {item.quote && (
          <p className="text-[11px] text-[#999] mt-1 italic truncate">"{item.quote}"</p>
        )}
        {item.cvLineId && (
          <p className="text-[10px] text-indigo-500 mt-1 font-medium">
            {isActive ? "↳ Highlighted in CV" : "↳ Click to highlight in CV"}
          </p>
        )}
      </div>
      <span className={`flex-shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded-md h-fit ${sev.cls}`}>
        {sev.label}
      </span>
    </div>
  );
}

function AccordionSection({
  section, items, activeFeedbackId, onFeedbackClick,
}: {
  section: typeof sections[0];
  items: FeedbackItem[];
  activeFeedbackId: string | null;
  onFeedbackClick: (id: string) => void;
}) {
  const [open, setOpen] = useState(section.defaultOpen ?? false);
  const urgentCount = items.filter((i) => i.severity === "high").length;

  return (
    <div className={`rounded-xl border overflow-hidden transition-colors duration-150 ${open ? "border-black/10" : "border-black/[0.06]"}`}>
      <div
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between px-3.5 py-3 cursor-pointer select-none hover:bg-black/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${section.bg}`}>
            <span className={`text-[11px] font-black ${section.countColor}`}>{items.length}</span>
          </div>
          <div>
            <p className="text-[13px] font-bold">{section.label}</p>
            <p className="text-[11px] text-[#999]">{section.desc}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {urgentCount > 0 && (
            <span className="text-[10px] font-bold bg-red-50 text-red-500 border border-red-100 px-2 py-0.5 rounded-full">
              {urgentCount} urgent
            </span>
          )}
          <svg
            className={`w-3.5 h-3.5 text-[#999] transition-transform duration-200 ${open ? "rotate-180" : ""}`}
            viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </div>

      <div
        className="overflow-hidden transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]"
        style={{ maxHeight: open ? `${items.length * 120}px` : "0" }}
      >
        <div className="px-3 pb-3 pt-0 border-t border-black/[0.05]">
          <div className="pt-2.5 flex flex-col gap-1.5">
            {items.map((item) => (
              <FeedbackItemRow
                key={item.id}
                item={item}
                isActive={activeFeedbackId === item.id}
                onClick={() => onFeedbackClick(item.id)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function FeedbackSidebar({ feedback, activeFeedbackId, onFeedbackClick }: FeedbackSidebarProps) {
  const urgentCount = Object.values(feedback).flat().filter((i) => i.severity === "high").length;

  return (
    <div className="bg-white rounded-2xl border border-black/[0.07] shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-[14px] font-bold tracking-tight">Feedback</h3>
          <p className="text-[12px] text-[#555] mt-0.5">Click any issue to highlight it in CV →</p>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
          <span className="text-[12px] font-semibold text-red-500">{urgentCount} urgent</span>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {sections.map((section) => (
          <AccordionSection
            key={section.key}
            section={section}
            items={feedback[section.key]}
            activeFeedbackId={activeFeedbackId}
            onFeedbackClick={onFeedbackClick}
          />
        ))}
      </div>
    </div>
  );
}