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

**ResumeIQ** is a Next.js 16 App Router frontend prototype for AI-powered resume analysis. It is currently frontend-only — upload, scoring, and AI suggestions are all simulated with mock data. There is no backend, database, or real PDF parsing.

### Data flow

1. User drops a PDF on `UploadDropzone` → `useFileUpload` simulates a multi-step pipeline (uploading → parsing → done) with random scores (40–70 range).
2. The result object is passed into `src/app/dashboard/page.tsx`, which distributes it to child components.
3. Mock analysis data lives in `src/lib/mockData.ts`: `mockAnalysis`, `mockCVSections`, and `feedbackCVMapping` (maps feedback IDs → CV line IDs).

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
├── ImproveDrawer          — slide-in: top 3 improvements + "Apply with AI" (stub)
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

## What's stubbed / not yet real

- PDF upload does not parse file content
- Scoring is random (40–70); analysis data comes from `mockData.ts`
- Login redirects after a 700 ms delay; no auth exists
- "Apply with AI" and Download/Share buttons are non-functional
- No backend, API routes, or persistence
