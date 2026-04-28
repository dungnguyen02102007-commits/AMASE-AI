"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { mockAnalysis, mockCVSections } from "@/lib/mockData";
import { ResumeAnalysis, CVSection, FeedbackCVMapping } from "@/types/resume";

import { ScoreCard } from "@/components/dashboard/ScoreCard";
import { ScoreBreakdown } from "@/components/dashboard/ScoreBreakdown";
import { FeedbackSidebar } from "@/components/dashboard/FeedbackSidebar";
import { ImprovementList } from "@/components/dashboard/ImprovementList";
import { CVPreview } from "@/components/cv/CVPreview";
import { ImproveDrawer } from "@/components/ui/ImproveDrawer";
import { TipsModal } from "@/components/ui/TipsModal";
import { UploadDropzone } from "@/components/ui/UploadDropzone";

import { useFeedbackHighlight } from "@/hooks/useFeedbackHighlights";
import { useFileUpload } from "@/hooks/useFileUpload";
import { useHistory } from "@/hooks/useHistory";
import { UserMenu } from "@/components/ui/UserMenu";

export default function DashboardPage() {
  // ── History (load via ?id=, save on upload) ────────────────────────────
  const searchParams = useSearchParams();
  const historyId = searchParams.get("id");
  const { add: addHistory, getById: getHistoryById } = useHistory();

  // ── Analysis + CV content state ───────────────────────────────────────
  // If URL has ?id=, hydrate from history on first render to avoid a
  // mock→real flash. Otherwise start with mock.
  const [analysis, setAnalysis] = useState<ResumeAnalysis>(() => {
    if (historyId) {
      const entry = getHistoryById(historyId);
      if (entry) return entry.analysis;
    }
    return mockAnalysis;
  });
  const [cvSections, setCvSections] = useState<CVSection[]>(() => {
    if (historyId) {
      const entry = getHistoryById(historyId);
      if (entry) return entry.cvSections;
    }
    return mockCVSections;
  });

  // ── Feedback ↔ CV interaction ─────────────────────────────────────────
  const feedbackMapping = useMemo<FeedbackCVMapping>(() => {
    const allItems = [
      ...analysis.feedback.action,
      ...analysis.feedback.specifics,
      ...analysis.feedback.overusage,
      ...analysis.feedback.avoided,
    ];
    return Object.fromEntries(
      allItems.map((item) => [
        item.id,
        item.cvLineId ? { cvLineId: item.cvLineId, sectionId: "" } : null,
      ])
    );
  }, [analysis.feedback]);

  const { activeFeedbackId, activeCVLineId, activate } = useFeedbackHighlight(feedbackMapping);

  // ── Panel toggles ──────────────────────────────────────────────────────
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  // ── Upload ─────────────────────────────────────────────────────────────
  const { upload, handleFile, reset: resetUpload, result: uploadResult } = useFileUpload();

  // Reload analysis when ?id= changes (e.g. user picks another entry from /history)
  useEffect(() => {
    if (!historyId) return;
    const entry = getHistoryById(historyId);
    if (entry) {
      setAnalysis(entry.analysis);
      setCvSections(entry.cvSections);
    }
  }, [historyId, getHistoryById]);

  // Commit upload result + persist to history
  useEffect(() => {
    if (uploadResult) {
      setAnalysis(uploadResult.analysis);
      setCvSections(uploadResult.cvSections);
      addHistory({
        fileName: upload.fileName ?? "resume.pdf",
        analysis: uploadResult.analysis,
        cvSections: uploadResult.cvSections,
      });
    }
  }, [uploadResult, addHistory, upload.fileName]);

  return (
    <>
      {/* ── Navbar ───────────────────────────────────────────────────── */}
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
          <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">
            Pro
          </span>
        </div>

        <div className="flex-1 flex justify-center">
          <div className="flex gap-0.5 bg-black/[0.05] rounded-[10px] p-[3px]">
            {[
              { label: "Dashboard", href: "/dashboard" },
              { label: "History", href: "/history" },
            ].map((tab, i) => (
              <Link
                key={tab.label}
                href={tab.href}
                className={
                  "text-[13px] font-semibold px-3.5 py-1.5 rounded-[7px] transition-all " +
                  (i === 0
                    ? "bg-white text-slate-800 shadow-sm"
                    : "text-slate-500 hover:text-slate-800 hover:bg-white/60")
                }
              >
                {tab.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => setModalOpen(true)}
            className="text-[12px] font-semibold text-slate-600 border border-slate-200 rounded-lg px-3 py-1.5 hover:bg-slate-50 transition-colors"
          >
            View Tips
          </button>
          <button
            onClick={() => setDrawerOpen(true)}
            className="text-[12px] font-semibold text-white bg-slate-900 hover:bg-black rounded-lg px-3 py-1.5 transition-colors"
          >
            Improve Resume
          </button>
          <UserMenu />
        </div>
      </nav>

      {/* ── Page header ───────────────────────────────────────────────── */}
      <div className="max-w-[1400px] mx-auto px-6 pt-8 pb-4">
        <div className="flex items-end justify-between gap-4 flex-wrap">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-widest text-indigo-500 mb-1">
              Resume Analysis
            </p>
            <h1 className="text-[22px] font-extrabold tracking-tight">Your Report is Ready</h1>
            <p className="text-[13px] text-slate-500 mt-1">
              Analyzed vs.{" "}
              <strong className="text-slate-700">{analysis.targetRole}</strong> roles ·{" "}
              {analysis.analysisDate}
            </p>
          </div>

          {/* Upload strip */}
          <div className="w-full sm:w-80">
            <UploadDropzone
              upload={upload}
              onFile={handleFile}
              onReset={resetUpload}
              compact
            />
          </div>
        </div>
      </div>

      {/* ── Main 2-column layout ──────────────────────────────────────── */}
      <div className="max-w-[1400px] mx-auto px-6 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] xl:grid-cols-[1fr_420px] gap-6">

          {/* LEFT: Dashboard */}
          <div className="flex flex-col gap-5">

            <ScoreCard
              score={analysis.score}
              maxScore={analysis.maxScore}
              candidateName={analysis.candidateName}
              targetRole={analysis.targetRole}
              analysisDate={analysis.analysisDate}
              percentile={analysis.percentile}
              issueCount={analysis.issueCount}
              scorePotential={analysis.scorePotential}
            />

            <ScoreBreakdown breakdown={analysis.breakdown} />

            <FeedbackSidebar
              feedback={analysis.feedback}
              activeFeedbackId={activeFeedbackId}
              onFeedbackClick={activate}
            />

            <ImprovementList
              improvements={analysis.improvements}
              onImproveClick={() => setDrawerOpen(true)}
            />

          </div>

          {/* RIGHT: Sticky CV Preview */}
          <div className="hidden lg:block">
            <CVPreview
              sections={cvSections}
              activeCVLineId={activeCVLineId}
              score={analysis.score}
              fileName={upload.fileName ?? "resume.pdf"}
            />
          </div>
        </div>

        {/* CV Preview on mobile (below dashboard) */}
        <div className="lg:hidden mt-6">
          <CVPreview
            sections={cvSections}
            activeCVLineId={activeCVLineId}
            score={analysis.score}
            fileName={upload.fileName ?? "resume.pdf"}
          />
        </div>
      </div>

      {/* ── Drawer + Modal ─────────────────────────────────────────────── */}
      <ImproveDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        improvements={analysis.improvements}
      />

      <TipsModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        feedback={analysis.feedback}
      />
    </>
  );
}
