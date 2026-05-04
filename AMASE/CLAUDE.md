# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev       # Start dev server at http://localhost:3000
npm run build     # Production build
npm start         # Serve production build
npm run lint      # ESLint via next lint
```

No test runner is configured yet.

## Architecture

**ResumeIQ** is a Next.js 16 App Router application for AI-powered resume analysis, backed by Supabase (auth + Postgres history) and the Anthropic Claude API.

### Data flow

1. User drops a PDF on `UploadDropzone` → `useFileUpload` POSTs to `/api/analyze`.
2. `/api/analyze` extracts text via `unpdf`, sends to Claude, and returns `{ analysis, cvSections }`.
3. The result lands in `dashboard/page.tsx`, which distributes it to child components and saves to Supabase history via `useHistory`.
4. Mock data in `src/lib/mockData.ts` is the default state before any PDF is uploaded.

### Feedback ↔ CV highlighting

The most distinctive pattern: clicking a feedback item in `FeedbackSidebar` highlights the corresponding CV line in `CVPreview`. This is wired through:

- `feedbackCVMapping` in `mockData.ts` — static lookup table
- `useFeedbackHighlights` hook — manages active feedback/CV state and provides `activate()`, `clear()`, `isActive()`, `cvLineState()` callbacks
- `CVPreview` applies amber (flagged) or indigo (active) border classes based on this state

### Key component relationships

```
dashboard/page.tsx
├── ScoreCard              — circular progress, grade, percentile
├── ScoreBreakdown         — Impact (max 50) / Presentation (30) / Competencies (20)
├── FeedbackSidebar        — 4 accordion sections; click → activates CV highlight
├── ImprovementList        — ranked 1–6 improvements with point gains
├── CVPreview              — sticky; highlights flagged/active lines
├── ImproveDrawer          — slide-in: top 3 improvements + "Apply All with AI" (calls /api/rewrite)
└── TipsModal              — categorized resume tips with personalized issues
```

### Scoring model

Scores decompose into three dimensions tracked in `ResumeAnalysis`:
- **Impact** — max 50 pts (action verbs, quantification, achievements)
- **Presentation** — max 30 pts (structure, formatting, length)
- **Competencies** — max 20 pts (keywords, skills alignment)

Color thresholds: red < 50, amber 50–75, green > 75.

### TypeScript types

All domain types are in `src/types/resume.ts`: `ResumeAnalysis`, `Feedback`, `CVSection`, `Improvement`, `UploadState`. Keep these as the source of truth when extending functionality.

## What's real vs. still pending

All core flows are live:
- PDF upload → real text extraction (`unpdf`) → Claude analysis (`/api/analyze`)
- AI rewrite via `/api/rewrite` (Apply All with AI in `ImproveDrawer`)
- Supabase email/password auth with middleware protection on `/dashboard` and `/history`
- History persisted in Supabase `history` table; `useHistory` hook migrates legacy localStorage on first load
- Download Improved — real PDF via `@react-pdf/renderer` (`src/lib/generateResumePdf.tsx`), dynamically imported
- Share button uses Web Share API on mobile / clipboard fallback on desktop

Remaining gaps:
- Share on desktop copies plain text — no shareable link
- `mockData.ts` is still the default shown before any PDF is uploaded
