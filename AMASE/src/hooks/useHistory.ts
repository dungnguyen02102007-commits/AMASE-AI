"use client";

import { useState, useEffect, useCallback } from "react";
import { HistoryEntry, ResumeAnalysis, CVSection } from "@/types/resume";

const STORAGE_KEY = "resumeiq:history";
const MAX_ENTRIES = 50;

// ── Storage helpers (SSR-safe) ────────────────────────────────────────────

function readStorage(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStorage(entries: HistoryEntry[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // Quota exceeded or storage unavailable — silently ignore
  }
}

function generateId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

// ── Hook ──────────────────────────────────────────────────────────────────

export interface AddHistoryParams {
  fileName: string;
  analysis: ResumeAnalysis;
  cvSections: CVSection[];
}

export interface UseHistoryReturn {
  entries: HistoryEntry[];
  add: (params: AddHistoryParams) => HistoryEntry;
  remove: (id: string) => void;
  clear: () => void;
  getById: (id: string) => HistoryEntry | undefined;
}

export function useHistory(): UseHistoryReturn {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  // Hydrate on mount (client-only)
  useEffect(() => {
    setEntries(readStorage());
  }, []);

  // Sync across tabs / windows
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) setEntries(readStorage());
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  const add = useCallback((params: AddHistoryParams): HistoryEntry => {
    const entry: HistoryEntry = {
      id: generateId(),
      fileName: params.fileName,
      createdAt: new Date().toISOString(),
      analysis: params.analysis,
      cvSections: params.cvSections,
    };
    setEntries((prev) => {
      const next = [entry, ...prev].slice(0, MAX_ENTRIES);
      writeStorage(next);
      return next;
    });
    return entry;
  }, []);

  const remove = useCallback((id: string) => {
    setEntries((prev) => {
      const next = prev.filter((e) => e.id !== id);
      writeStorage(next);
      return next;
    });
  }, []);

  const clear = useCallback(() => {
    setEntries([]);
    writeStorage([]);
  }, []);

  // Read fresh from storage so it works even before the state has hydrated
  // (e.g. on first render of /dashboard?id=xxx after opening from /history)
  const getById = useCallback(
    (id: string): HistoryEntry | undefined =>
      readStorage().find((e) => e.id === id),
    []
  );

  return { entries, add, remove, clear, getById };
}
