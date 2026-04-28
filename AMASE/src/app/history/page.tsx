"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useHistory } from "@/hooks/useHistory";
import { HistoryEntry } from "@/types/resume";
import { UserMenu } from "@/components/ui/UserMenu";

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return iso;
  }
}

function ScoreBadge({ score }: { score: number }) {
  const cls =
    score < 50 ? "bg-red-50 text-red-600 border-red-100"
    : score < 75 ? "bg-amber-50 text-amber-700 border-amber-100"
    : "bg-emerald-50 text-emerald-700 border-emerald-100";
  return (
    <span className={"text-[12px] font-bold px-2.5 py-1 rounded-lg border tabular-nums flex-shrink-0 " + cls}>
      {score}/100
    </span>
  );
}

function HistoryRow({
  entry, onOpen, onDelete,
}: {
  entry: HistoryEntry;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div
      onClick={() => onOpen(entry.id)}
      className="group flex items-center gap-4 bg-white rounded-2xl border border-black/[0.07] shadow-sm p-4 hover:border-indigo-200 hover:shadow-md transition-all cursor-pointer"
    >
      <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center flex-shrink-0">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-400">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-bold text-slate-800 truncate">{entry.fileName}</p>
        <p className="text-[11px] text-slate-500 mt-0.5 truncate">
          {entry.analysis.candidateName} · {entry.analysis.targetRole}
        </p>
      </div>
      <div className="hidden sm:flex flex-col items-end gap-0.5 flex-shrink-0">
        <span className="text-[11px] text-slate-400 font-mono">{formatDate(entry.createdAt)}</span>
        <span className="text-[10px] text-slate-400">{entry.analysis.issueCount} issues</span>
      </div>
      <ScoreBadge score={entry.analysis.score} />
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(entry.id); }}
        className="w-8 h-8 rounded-lg hover:bg-red-50 hover:text-red-500 text-slate-400 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100 focus:opacity-100"
        aria-label={"Delete " + entry.fileName}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-2">
      {[0, 1, 2].map((i) => (
        <div key={i} className="flex items-center gap-4 bg-white rounded-2xl border border-black/[0.07] shadow-sm p-4">
          <div className="w-10 h-10 rounded-xl bg-slate-100 animate-pulse flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="h-3 w-2/3 bg-slate-100 rounded animate-pulse" />
            <div className="h-2.5 w-1/2 bg-slate-100 rounded animate-pulse mt-2" />
          </div>
          <div className="h-6 w-16 bg-slate-100 rounded-lg animate-pulse" />
        </div>
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="bg-white rounded-2xl border border-black/[0.07] shadow-sm p-12 text-center">
      <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-slate-400">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      </div>
      <h3 className="text-[15px] font-bold text-slate-800">No history yet</h3>
      <p className="text-[13px] text-slate-500 mt-1.5 max-w-sm mx-auto">
        Upload a resume on the dashboard and it will appear here.
      </p>
      <Link href="/dashboard" className="inline-block mt-5 text-[13px] font-semibold text-white bg-slate-900 hover:bg-black rounded-xl px-4 py-2 transition-colors">
        Analyze a resume →
      </Link>
    </div>
  );
}

function ClearConfirmModal({
  count, onCancel, onConfirm,
}: {
  count: number;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 bg-black/30 backdrop-blur-[2px] flex items-center justify-center p-4" onClick={onCancel}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-[15px] font-bold tracking-tight">Clear all history?</h2>
        <p className="text-[13px] text-slate-500 mt-1.5">
          This will delete {count} saved {count === 1 ? "analysis" : "analyses"}. This cannot be undone.
        </p>
        <div className="flex gap-2 mt-5">
          <button onClick={onCancel} className="flex-1 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-[13px] font-semibold transition-colors">
            Cancel
          </button>
          <button onClick={onConfirm} className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-[13px] font-semibold transition-colors">
            Clear all
          </button>
        </div>
      </div>
    </div>
  );
}

export default function HistoryPage() {
  const router = useRouter();
  const { entries, loading, error, migratedCount, remove, clear } = useHistory();
  const [confirmClear, setConfirmClear] = useState(false);

  return (
    <>
      <nav className="sticky top-0 z-50 h-14 bg-white border-b border-black/[0.07] flex items-center px-5 gap-3">
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
          <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">Pro</span>
        </div>
        <div className="flex-1 flex justify-center">
          <div className="flex gap-0.5 bg-black/[0.05] rounded-[10px] p-[3px]">
            {[
              { label: "Dashboard", href: "/dashboard", active: false },
              { label: "History", href: "/history", active: true },
            ].map((tab) => (
              <Link key={tab.label} href={tab.href} className={"text-[13px] font-semibold px-3.5 py-1.5 rounded-[7px] transition-all " + (tab.active ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-800 hover:bg-white/60")}>
                {tab.label}
              </Link>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Link href="/dashboard" className="text-[12px] font-semibold text-white bg-slate-900 hover:bg-black rounded-lg px-3 py-1.5 transition-colors">
            New Analysis
          </Link>
          <UserMenu />
        </div>
      </nav>

      <div className="max-w-[1100px] mx-auto px-6 pt-8 pb-16">
        <div className="flex items-end justify-between gap-4 mb-6 flex-wrap">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-widest text-indigo-500 mb-1">History</p>
            <h1 className="text-[22px] font-extrabold tracking-tight">Past Analyses</h1>
            <p className="text-[13px] text-slate-500 mt-1">
              {loading ? "Loading..." : entries.length === 0 ? "No analyses yet" : entries.length + " saved - synced to your account"}
            </p>
          </div>
          {!loading && entries.length > 0 && (
            <button onClick={() => setConfirmClear(true)} className="text-[12px] font-semibold text-slate-600 border border-slate-200 rounded-lg px-3 py-1.5 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-colors">
              Clear all
            </button>
          )}
        </div>

        {migratedCount > 0 && (
          <div className="mb-4 px-4 py-3 rounded-xl bg-emerald-50 border border-emerald-100 text-[12.5px] text-emerald-800">
            <span className="font-semibold">Welcome back.</span> Moved {migratedCount} {migratedCount === 1 ? "entry" : "entries"} from your browser to your account.
          </div>
        )}

        {error && (
          <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-[12.5px] text-red-700">
            <span className="font-semibold">Could not load history:</span> {error}
          </div>
        )}

        {loading ? (
          <LoadingSkeleton />
        ) : entries.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="flex flex-col gap-2">
            {entries.map((entry) => (
              <HistoryRow
                key={entry.id}
                entry={entry}
                onOpen={(id) => router.push("/dashboard?id=" + id)}
                onDelete={(id) => { void remove(id); }}
              />
            ))}
          </div>
        )}
      </div>

      {confirmClear && (
        <ClearConfirmModal
          count={entries.length}
          onCancel={() => setConfirmClear(false)}
          onConfirm={() => { void clear(); setConfirmClear(false); }}
        />
      )}
    </>
  );
}
