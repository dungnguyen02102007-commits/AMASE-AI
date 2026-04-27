"use client";

import { useState, useCallback } from "react";
import { FeedbackCVMapping } from "@/types/resume";
import { feedbackCVMapping } from "@/lib/mockData";

export interface FeedbackHighlightState {
  activeFeedbackId: string | null;
  activeCVLineId: string | null;
}

export interface UseFeedbackHighlightReturn extends FeedbackHighlightState {
  activate: (feedbackId: string) => void;
  clear: () => void;
  isActive: (feedbackId: string) => boolean;
  cvLineState: (cvLineId: string, isDefaultHighlighted?: boolean) => "active" | "highlighted" | "normal";
}

export function useFeedbackHighlight(
  feedbackMapping?: FeedbackCVMapping
): UseFeedbackHighlightReturn {
  const [activeFeedbackId, setActiveFeedbackId] = useState<string | null>(null);
  const [activeCVLineId, setActiveCVLineId] = useState<string | null>(null);

  const activate = useCallback((feedbackId: string) => {
    // Toggle off if already active
    if (activeFeedbackId === feedbackId) {
      setActiveFeedbackId(null);
      setActiveCVLineId(null);
      return;
    }

    const mapping = (feedbackMapping ?? feedbackCVMapping)[feedbackId];
    const cvLineId = mapping?.cvLineId ?? null;

    setActiveFeedbackId(feedbackId);
    setActiveCVLineId(cvLineId);

    // Scroll CV panel to the target line
    if (cvLineId) {
      // Use rAF so state flushes before we measure DOM positions
      requestAnimationFrame(() => {
        const line = document.getElementById(cvLineId);
        const scroller = document.getElementById("cv-scroll-container");
        if (!line || !scroller) return;

        const lineTop =
          line.getBoundingClientRect().top -
          scroller.getBoundingClientRect().top +
          scroller.scrollTop -
          96; // offset so the line isn't flush to the top

        scroller.scrollTo({ top: Math.max(0, lineTop), behavior: "smooth" });
      });
    }
  }, [activeFeedbackId, feedbackMapping]);

  const clear = useCallback(() => {
    setActiveFeedbackId(null);
    setActiveCVLineId(null);
  }, []);

  const isActive = useCallback(
    (feedbackId: string) => activeFeedbackId === feedbackId,
    [activeFeedbackId]
  );

  const cvLineState = useCallback(
    (cvLineId: string, isDefaultHighlighted = false): "active" | "highlighted" | "normal" => {
      if (cvLineId === activeCVLineId) return "active";
      if (isDefaultHighlighted) return "highlighted";
      return "normal";
    },
    [activeCVLineId]
  );

  return { activeFeedbackId, activeCVLineId, activate, clear, isActive, cvLineState };
}