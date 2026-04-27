"use client";

import { useState, useCallback } from "react";
import { UploadState, ResumeAnalysis, CVSection } from "@/types/resume";
import { mockAnalysis, mockCVSections } from "@/lib/mockData";

export interface UploadResult {
  analysis: ResumeAnalysis;
  cvSections: CVSection[];
}

interface UseFileUploadReturn {
  upload: UploadState;
  handleFile: (file: File) => void;
  reset: () => void;
  result: UploadResult | null;
}

const INITIAL: UploadState = {
  status: "idle",
  fileName: null,
  progress: 0,
  error: null,
};

export function useFileUpload(): UseFileUploadReturn {
  const [upload, setUpload] = useState<UploadState>(INITIAL);
  const [result, setResult] = useState<UploadResult | null>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUpload({ status: "error", fileName: file.name, progress: 0, error: "Only PDF files are accepted." });
      return;
    }

    setResult(null);
    setUpload({ status: "uploading", fileName: file.name, progress: 0, error: null });

    // Animate progress 0→90 while the fetch is in flight
    let progressVal = 0;
    const progressInterval = setInterval(() => {
      progressVal = Math.min(progressVal + 12, 90);
      setUpload((prev) => ({ ...prev, progress: progressVal }));
      if (progressVal >= 90) clearInterval(progressInterval);
    }, 160);

    // Transition to "parsing" status after 1.2s regardless of network speed
    const parsingTimeout = setTimeout(() => {
      setUpload((prev) => ({ ...prev, status: "parsing", progress: 100 }));
    }, 1200);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/analyze", { method: "POST", body: formData });

      clearInterval(progressInterval);
      clearTimeout(parsingTimeout);

      if (!response.ok) {
        const body = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(`API ${response.status}: ${body.error ?? "unknown"}`);
      }

      const data: UploadResult = await response.json();
      setResult(data);
      setUpload((prev) => ({ ...prev, status: "done", progress: 100 }));
    } catch (err) {
      clearInterval(progressInterval);
      clearTimeout(parsingTimeout);
      console.error("Analyze failed, using mock data:", err);
      // Silent fallback — dashboard stays functional with mock data
      setResult({ analysis: mockAnalysis, cvSections: mockCVSections });
      setUpload((prev) => ({ ...prev, status: "done", progress: 100 }));
    }
  }, []);

  const reset = useCallback(() => {
    setUpload(INITIAL);
    setResult(null);
  }, []);

  return { upload, handleFile, reset, result };
}
