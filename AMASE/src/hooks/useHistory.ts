"use client";

import { useState, useEffect, useCallback } from "react";
import { HistoryEntry, ResumeAnalysis, CVSection } from "@/types/resume";
import { createClient } from "@/utils/supabase/client";

const LOCAL_STORAGE_KEY = "resumeiq:history"; // legacy — kept for one-time migration
const MAX_ENTRIES = 50;

// Shape returned by Supabase
interface DbRow {
  id: string;
  user_id: string;
  file_name: string;
  created_at: string;
  analysis: ResumeAnalysis;
  cv_sections: CVSection[];
}

function rowToEntry(row: DbRow): HistoryEntry {
  return {
    id: row.id,
    fileName: row.file_name,
    createdAt: row.created_at,
    analysis: row.analysis,
    cvSections: row.cv_sections,
  };
}

// ── Legacy localStorage helpers (only used to migrate then forget) ────────

function readLegacyLocalStorage(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function clearLegacyLocalStorage(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(LOCAL_STORAGE_KEY);
  } catch {
    // ignore
  }
}

// ── Public hook ───────────────────────────────────────────────────────────

export interface AddHistoryParams {
  fileName: string;
  analysis: ResumeAnalysis;
  cvSections: CVSection[];
}

export interface UseHistoryReturn {
  entries: HistoryEntry[];
  loading: boolean;
  error: string | null;
  migratedCount: number;
  add: (params: AddHistoryParams) => Promise<HistoryEntry | null>;
  remove: (id: string) => Promise<void>;
  clear: () => Promise<void>;
  getById: (id: string) => Promise<HistoryEntry | undefined>;
}

export function useHistory(): UseHistoryReturn {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [migratedCount, setMigratedCount] = useState(0);

  // Load entries on mount, with one-shot localStorage migration
  useEffect(() => {
    let cancelled = false;
    const supabase = createClient();

    async function load() {
      setLoading(true);
      setError(null);

      const userRes = await supabase.auth.getUser();
      const user = userRes.data.user;

      if (!user) {
        if (!cancelled) {
          setEntries([]);
          setLoading(false);
        }
        return;
      }

      // Step 1: Migrate any legacy localStorage entries to Postgres
      const legacy = readLegacyLocalStorage();
      if (legacy.length > 0) {
        const rows = legacy.map((e) => ({
          user_id: user.id,
          file_name: e.fileName,
          created_at: e.createdAt,
          analysis: e.analysis,
          cv_sections: e.cvSections,
        }));
        const { error: insertErr } = await supabase.from("history").insert(rows);
        if (!insertErr) {
          clearLegacyLocalStorage();
          if (!cancelled) setMigratedCount(legacy.length);
        }
      }

      // Step 2: Fetch entries from Postgres
      const { data, error: fetchErr } = await supabase
        .from("history")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(MAX_ENTRIES);

      if (cancelled) return;

      if (fetchErr) {
        setError(fetchErr.message);
        setEntries([]);
      } else {
        const rows = (data ?? []) as DbRow[];
        setEntries(rows.map(rowToEntry));
      }
      setLoading(false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const add = useCallback(
    async (params: AddHistoryParams): Promise<HistoryEntry | null> => {
      const supabase = createClient();
      const userRes = await supabase.auth.getUser();
      const user = userRes.data.user;
      if (!user) return null;

      const { data, error: insertErr } = await supabase
        .from("history")
        .insert({
          user_id: user.id,
          file_name: params.fileName,
          analysis: params.analysis,
          cv_sections: params.cvSections,
        })
        .select()
        .single();

      if (insertErr || !data) return null;
      const entry = rowToEntry(data as DbRow);
      setEntries((prev) => [entry, ...prev].slice(0, MAX_ENTRIES));
      return entry;
    },
    []
  );

  const remove = useCallback(async (id: string): Promise<void> => {
    const supabase = createClient();
    const { error: deleteErr } = await supabase.from("history").delete().eq("id", id);
    if (!deleteErr) {
      setEntries((prev) => prev.filter((e) => e.id !== id));
    }
  }, []);

  const clear = useCallback(async (): Promise<void> => {
    const supabase = createClient();
    const userRes = await supabase.auth.getUser();
    const user = userRes.data.user;
    if (!user) return;
    const { error: deleteErr } = await supabase
      .from("history")
      .delete()
      .eq("user_id", user.id);
    if (!deleteErr) setEntries([]);
  }, []);

  const getById = useCallback(
    async (id: string): Promise<HistoryEntry | undefined> => {
      const supabase = createClient();
      const { data, error: fetchErr } = await supabase
        .from("history")
        .select("*")
        .eq("id", id)
        .single();
      if (fetchErr || !data) return undefined;
      return rowToEntry(data as DbRow);
    },
    []
  );

  return { entries, loading, error, migratedCount, add, remove, clear, getById };
}
