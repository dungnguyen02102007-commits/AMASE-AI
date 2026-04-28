"use client";

import { useEffect, useRef, useState } from "react";
import { createClient } from "@/utils/supabase/client";

function initialsFor(email: string | undefined): string {
  if (!email) return "..";
  const local = email.split("@")[0];
  const parts = local.split(/[._-]/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return local.slice(0, 2).toUpperCase();
}

export function UserMenu() {
  const [email, setEmail] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    const supabase = createClient();
    supabase.auth.getUser().then((res: { data: { user: { email?: string } | null } }) => {
      if (!cancelled) setEmail(res.data.user?.email ?? null);
    });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white text-[11px] font-bold cursor-pointer hover:opacity-90 transition-opacity"
        aria-label="Account menu"
      >
        {initialsFor(email ?? undefined)}
      </button>

      {open && (
        <div className="absolute right-0 top-10 w-60 bg-white rounded-xl border border-black/[0.07] shadow-md overflow-hidden z-50">
          <div className="px-4 py-3 border-b border-slate-100">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Signed in as</p>
            <p className="text-[12.5px] font-semibold text-slate-800 truncate mt-0.5">
              {email ?? "Loading..."}
            </p>
          </div>
          <form action="/auth/signout" method="POST">
            <button
              type="submit"
              className="w-full text-left px-4 py-2.5 text-[12.5px] font-semibold text-slate-700 hover:bg-slate-50 hover:text-red-600 transition-colors flex items-center gap-2"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              Sign out
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
