"use client";

import { CVSection, CVSectionContent, CVBulletContent } from "@/types/resume";

interface CVPreviewProps {
  sections: CVSection[];
  activeCVLineId: string | null;
  score: number;
  fileName?: string;
}

function CVHeader({ content }: { content: CVSectionContent }) {
  return (
    <div className="text-center pb-5 mb-5 border-b-2 border-slate-800">
      <h1 className="text-[22px] font-black tracking-tight text-slate-900">
        {content.heading}
      </h1>
      {content.subheading && (
        <p className="text-[13px] font-medium text-slate-500 mt-1">{content.subheading}</p>
      )}
      {content.text && (
        <p className="text-[11px] text-slate-400 mt-1.5 font-mono">{content.text}</p>
      )}
    </div>
  );
}

function CVTextBlock({ content }: { content: CVSectionContent }) {
  return (
    <p className="text-[12.5px] leading-relaxed text-slate-600">
      {content.text ?? content.heading}
    </p>
  );
}

function CVBulletItem({ bullet, isActive }: { bullet: CVBulletContent; isActive: boolean }) {
  return (
    <li className="flex items-start gap-2">
      <span className="mt-[7px] w-[5px] h-[5px] rounded-full bg-slate-400 flex-shrink-0" />
      <span
        id={bullet.id}
        className={[
          "text-[12px] leading-relaxed block rounded-r transition-all duration-300 ease-out",
          isActive
            ? "bg-indigo-50 border-l-2 border-indigo-500 pl-2 pr-1 py-0.5 text-slate-800 shadow-sm"
            : bullet.highlighted
            ? "bg-amber-50 border-l-2 border-amber-400 pl-2 pr-1 py-0.5 text-slate-700"
            : "text-slate-600",
        ].filter(Boolean).join(" ")}
      >
        {bullet.text}
      </span>
    </li>
  );
}

function CVExperience({
  content,
  activeCVLineId,
}: {
  content: CVSectionContent;
  activeCVLineId: string | null;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-[13px] font-bold text-slate-800">{content.heading}</span>
        {content.date && (
          <span className="text-[11px] font-mono text-slate-400 flex-shrink-0">{content.date}</span>
        )}
      </div>
      {(content.company || content.location) && (
        <p className="text-[12px] italic text-slate-500 mt-0.5">
          {[content.company, content.location].filter(Boolean).join(" · ")}
        </p>
      )}
      {content.subheading && !content.company && (
        <p className="text-[12px] italic text-slate-500 mt-0.5">{content.subheading}</p>
      )}
      {content.bullets && content.bullets.length > 0 && (
        <ul className="mt-2.5 space-y-1.5 ml-3">
          {content.bullets.map((bullet) => (
            <CVBulletItem
              key={bullet.id}
              bullet={bullet}
              isActive={activeCVLineId === bullet.id}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function CVEducation({ content }: { content: CVSectionContent }) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-[13px] font-bold text-slate-800">{content.heading}</span>
        {content.date && (
          <span className="text-[11px] font-mono text-slate-400 flex-shrink-0">{content.date}</span>
        )}
      </div>
      {content.subheading && (
        <p className="text-[12px] italic text-slate-500 mt-0.5">{content.subheading}</p>
      )}
      {content.text && (
        <p className="text-[12px] text-slate-400 mt-1">{content.text}</p>
      )}
    </div>
  );
}

function CVSectionBlock({
  section,
  activeCVLineId,
}: {
  section: CVSection;
  activeCVLineId: string | null;
}) {
  const { type, title, content } = section;
  if (type === "header") return <CVHeader content={content} />;
  return (
    <div className="mb-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[9.5px] font-black uppercase tracking-[0.12em] text-slate-700 whitespace-nowrap">
          {title}
        </span>
        <span className="flex-1 h-[1.5px] bg-slate-800" />
      </div>
      {type === "experience" && <CVExperience content={content} activeCVLineId={activeCVLineId} />}
      {(type === "summary" || type === "skills") && <CVTextBlock content={content} />}
      {type === "education" && <CVEducation content={content} />}
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color = score < 50 ? "bg-red-500" : score < 75 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <span className={"text-[11px] font-bold text-white px-2.5 py-0.5 rounded-full " + color}>
      {score} / 100
    </span>
  );
}

export function CVPreview({ sections, activeCVLineId, score, fileName = "resume.pdf" }: CVPreviewProps) {
  return (
    <div className="sticky top-6 flex flex-col">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden flex flex-col">
        <div className="bg-slate-800 px-5 py-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
              <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            </div>
            <span className="text-[11px] text-slate-400 font-mono ml-2 truncate max-w-[160px]">
              {fileName}
            </span>
          </div>
          <ScoreBadge score={score} />
        </div>

        <div className="px-4 py-2 bg-amber-50 border-b border-amber-100 flex items-center gap-3 flex-shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm border-l-2 border-amber-400 bg-amber-100 flex-shrink-0 inline-block" />
            <span className="text-[10px] text-amber-700 font-medium">Flagged</span>
          </div>
          <span className="text-amber-300 text-[10px]">·</span>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm border-l-2 border-indigo-500 bg-indigo-50 flex-shrink-0 inline-block" />
            <span className="text-[10px] text-indigo-600 font-medium">Selected issue</span>
          </div>
          {activeCVLineId && (
            <span className="text-[10px] text-indigo-600 font-semibold ml-auto animate-pulse">
              ↑ Scrolled to highlight
            </span>
          )}
        </div>

        <div
          id="cv-scroll-container"
          className="overflow-y-auto"
          style={{ maxHeight: "calc(100vh - 240px)", scrollbarWidth: "thin" }}
        >
          <div className="p-6 text-slate-800">
            {sections.map((section) => (
              <CVSectionBlock
                key={section.id}
                section={section}
                activeCVLineId={activeCVLineId}
              />
            ))}
          </div>
        </div>

        <div className="px-4 py-3 bg-slate-50 border-t border-slate-100 flex gap-2 flex-shrink-0">
          <button className="flex-1 py-2 rounded-lg bg-slate-800 hover:bg-slate-900 text-white text-[12px] font-semibold transition-colors">
            Download Improved
          </button>
          <button className="px-3 py-2 rounded-lg border border-slate-200 hover:bg-white text-slate-600 text-[12px] font-semibold transition-colors">
            Share
          </button>
        </div>
      </div>
    </div>
  );
}