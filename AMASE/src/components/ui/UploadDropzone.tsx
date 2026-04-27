"use client";

import { useCallback, useRef, useState } from "react";
import { UploadState } from "@/types/resume";

interface UploadDropzoneProps {
  upload: UploadState;
  onFile: (file: File) => void;
  onReset: () => void;
  compact?: boolean;
}

export function UploadDropzone({ upload, onFile, onReset, compact = false }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) onFile(file);
    },
    [onFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setIsDragging(false), []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onFile(file);
      // Reset input so same file can be re-uploaded
      e.target.value = "";
    },
    [onFile]
  );

  // ── Idle / drag state ─────────────────────────────────────────────────
  if (upload.status === "idle" || upload.status === "error") {
    return (
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={[
          "relative flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-200 select-none",
          compact ? "py-6 px-4" : "py-12 px-6",
          isDragging
            ? "border-indigo-400 bg-indigo-50/60 scale-[1.01]"
            : upload.status === "error"
            ? "border-red-300 bg-red-50/40 hover:border-red-400"
            : "border-slate-200 bg-slate-50/50 hover:border-indigo-300 hover:bg-indigo-50/30",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleInputChange}
        />

        {/* Icon */}
        <div className={`rounded-xl flex items-center justify-center ${compact ? "w-10 h-10" : "w-12 h-12"} ${upload.status === "error" ? "bg-red-100" : "bg-white shadow-sm border border-slate-100"}`}>
          {upload.status === "error" ? (
            <svg className="w-5 h-5 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          ) : (
            <svg className={`text-slate-400 ${compact ? "w-5 h-5" : "w-6 h-6"}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="18" x2="12" y2="12" />
              <line x1="9" y1="15" x2="12" y2="12" />
              <line x1="15" y1="15" x2="12" y2="12" />
            </svg>
          )}
        </div>

        {/* Text */}
        <div className="text-center">
          {upload.status === "error" ? (
            <>
              <p className="text-[13px] font-semibold text-red-600">{upload.error}</p>
              <p className="text-[11px] text-red-400 mt-0.5">Click to try again</p>
            </>
          ) : (
            <>
              <p className={`font-semibold text-slate-700 ${compact ? "text-[12px]" : "text-[13px]"}`}>
                {isDragging ? "Drop your PDF here" : "Drop PDF or click to upload"}
              </p>
              <p className={`text-slate-400 mt-0.5 ${compact ? "text-[10px]" : "text-[11px]"}`}>
                PDF only · Max 10MB
              </p>
            </>
          )}
        </div>
      </div>
    );
  }

  // ── Uploading / parsing state ─────────────────────────────────────────
  if (upload.status === "uploading" || upload.status === "parsing") {
    const isParsing = upload.status === "parsing";
    return (
      <div className={`flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white ${compact ? "p-4" : "p-6"}`}>
        {/* File name row */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-indigo-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[12px] font-semibold text-slate-800 truncate">{upload.fileName}</p>
            <p className="text-[11px] text-indigo-500 font-medium mt-0.5">
              {isParsing ? "Analyzing resume with AI…" : `Uploading… ${upload.progress}%`}
            </p>
          </div>
          {/* Spinner */}
          <svg className="w-4 h-4 text-indigo-400 animate-spin flex-shrink-0" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        </div>

        {/* Progress bar */}
        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-indigo-500 transition-all duration-300"
            style={{ width: isParsing ? "100%" : `${upload.progress}%` }}
          />
        </div>

        {/* Step indicators */}
        <div className="flex items-center gap-4">
          {["Upload", "Parse", "Analyze"].map((step, i) => {
            const done = (i === 0 && !isParsing && upload.progress === 100) ||
              (i === 0 && isParsing) || (i === 1 && isParsing);
            const active = (i === 0 && !isParsing) || (i === 1 && isParsing && upload.progress === 100);
            return (
              <div key={step} className="flex items-center gap-1.5">
                <div className={`w-4 h-4 rounded-full flex items-center justify-center ${done ? "bg-indigo-500" : active ? "bg-indigo-100 border border-indigo-300" : "bg-slate-100"}`}>
                  {done && (
                    <svg className="w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                  {active && <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />}
                </div>
                <span className={`text-[10px] font-semibold ${done || active ? "text-indigo-600" : "text-slate-400"}`}>{step}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // ── Done state ────────────────────────────────────────────────────────
  return (
    <div className={`flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 ${compact ? "p-4" : "p-5"}`}>
      <div className="w-9 h-9 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
        <svg className="w-4 h-4 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[12px] font-semibold text-emerald-800 truncate">{upload.fileName}</p>
        <p className="text-[11px] text-emerald-600 mt-0.5">Analysis complete · Score updated</p>
      </div>
      <button
        onClick={onReset}
        className="text-[11px] font-semibold text-emerald-700 hover:text-emerald-900 border border-emerald-200 hover:border-emerald-400 px-2.5 py-1 rounded-lg transition-colors flex-shrink-0"
      >
        Upload new
      </button>
    </div>
  );
}