import Anthropic from "@anthropic-ai/sdk";
import { extractText, getDocumentProxy } from "unpdf";
import { ResumeAnalysis, CVSection, FeedbackItem } from "@/types/resume";
import { createClient } from "@/utils/supabase/server";

export const runtime = "nodejs";

function buildPrompt(resumeText: string): string {
  const date = new Date().toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return `You are an expert resume analyst. Analyze the resume text below and return a JSON object.

CRITICAL RULES:
1. Return ONLY valid JSON. No markdown, no code fences, no explanation.
2. breakdown.impact + breakdown.presentation + breakdown.competencies MUST equal score exactly.
3. Scoring caps: impact ≤ 50, presentation ≤ 30, competencies ≤ 20.
4. Every cvLineId value in feedback items MUST match a bullet id in cvSections exactly.
5. Bullet ids use the pattern "cvl-job{N}-{M}" (e.g. first job first bullet = "cvl-job1-0").
6. Only set cvLineId when the feedback item refers to a specific bullet point.

Return this exact JSON shape:
{
  "analysis": {
    "candidateName": "string — full name from resume",
    "targetRole": "string — inferred seniority + role title",
    "analysisDate": "${date}",
    "score": number (0–100),
    "maxScore": 100,
    "percentile": number (0–99),
    "issueCount": number,
    "scorePotential": { "low": number, "high": number },
    "breakdown": { "impact": number (0–50), "presentation": number (0–30), "competencies": number (0–20) },
    "feedback": {
      "action":    [FeedbackItem],
      "specifics": [FeedbackItem],
      "overusage": [FeedbackItem],
      "avoided":   [FeedbackItem]
    },
    "improvements": [Improvement],
    "insights":     [AIInsight]
  },
  "cvSections": [CVSection]
}

FeedbackItem: { "id": "a1"|"s1"|"o1"|"av1"|..., "text": string, "quote"?: string, "severity": "high"|"medium"|"low", "cvLineId"?: string }
  — sequential ids per category: action → a1,a2,...; specifics → s1,s2,...; overusage → o1,...; avoided → av1,...
  — generate 2–5 items per category

Improvement: { "id": "imp1"|..., "rank": number, "category": string, "suggestion": string, "impact": "high"|"medium"|"low", "pointsGain": string }
  — generate 5–6 items ranked by impact

AIInsight: { "id": "i1"|..., "title": string, "detail": string, "severity": "high"|"medium"|"low", "feedbackId"?: string, "isQuickWin"?: boolean }
  — generate 5–8 items; mark quick wins (≤ 5 min to fix) with isQuickWin: true

CVSection: { "id": string, "title": string, "type": "header"|"summary"|"experience"|"skills"|"education", "content": CVSectionContent }
  — ids: cv-header, cv-summary, cv-job1, cv-job2, ..., cv-skills, cv-education
  — For experience sections include ALL bullet points from the resume as separate bullet objects
  — set highlighted: true on bullets whose id appears as a cvLineId in any feedback item

CVSectionContent: { "heading": string, "subheading"?: string, "text"?: string, "company"?: string, "location"?: string, "date"?: string, "bullets"?: [{ "id": string, "text": string, "highlighted"?: boolean }] }

SCORING GUIDANCE:
- Be honest — most resumes score 30–60; don't inflate
- issueCount = total feedback items across all four categories
- scorePotential.low = score after fixing the top 2–3 issues
- scorePotential.high = score after fixing all issues (cap at 95)
- breakdown.impact + breakdown.presentation + breakdown.competencies must add up to score exactly

RESUME TEXT:
---
${resumeText}
---`;
}

function enforceIntegrity(
  analysis: ResumeAnalysis,
  cvSections: CVSection[]
): void {
  // Cap breakdown dimensions
  analysis.breakdown.impact = Math.min(50, Math.max(0, analysis.breakdown.impact));
  analysis.breakdown.presentation = Math.min(30, Math.max(0, analysis.breakdown.presentation));
  analysis.breakdown.competencies = Math.min(20, Math.max(0, analysis.breakdown.competencies));

  // Override score to match breakdown sum — guarantees ScoreCard === ScoreBreakdown
  analysis.score = analysis.breakdown.impact + analysis.breakdown.presentation + analysis.breakdown.competencies;

  // Derive highlighted from actual cvLineId references (more reliable than Claude's output)
  const allItems: FeedbackItem[] = [
    ...analysis.feedback.action,
    ...analysis.feedback.specifics,
    ...analysis.feedback.overusage,
    ...analysis.feedback.avoided,
  ];
  const referencedIds = new Set(
    allItems.map((item) => item.cvLineId).filter(Boolean) as string[]
  );

  for (const section of cvSections) {
    if (section.content.bullets) {
      for (const bullet of section.content.bullets) {
        bullet.highlighted = referencedIds.has(bullet.id);
      }
    }
  }
}

export async function POST(request: Request): Promise<Response> {
  // Auth gate: only signed-in users can spend our Anthropic budget.
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const client = new Anthropic();
  try {
    const formData = await request.formData();
    const file = formData.get("file");

    if (!(file instanceof File)) {
      return Response.json({ error: "No file provided" }, { status: 400 });
    }
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return Response.json({ error: "Only PDF files are accepted" }, { status: 400 });
    }

    const buffer = await file.arrayBuffer();

    const pdf = await getDocumentProxy(new Uint8Array(buffer));
    const { text } = await extractText(pdf, { mergePages: true });
    const resumeText = text.slice(0, 12000);

    if (!resumeText.trim()) {
      return Response.json({ error: "Could not extract text from PDF" }, { status: 422 });
    }

    const message = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 4096,
      messages: [{ role: "user", content: buildPrompt(resumeText) }],
    });

    const textBlock = message.content.find((b) => b.type === "text");
    if (!textBlock || textBlock.type !== "text") {
      return Response.json({ error: "Unexpected response from AI" }, { status: 502 });
    }

    let result: { analysis: ResumeAnalysis; cvSections: CVSection[] };
    try {
      result = JSON.parse(textBlock.text);
    } catch {
      return Response.json({ error: "AI returned malformed JSON" }, { status: 502 });
    }

    enforceIntegrity(result.analysis, result.cvSections);

    return Response.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("[/api/analyze]", message);
    return Response.json({ error: message }, { status: 500 });
  }
}
