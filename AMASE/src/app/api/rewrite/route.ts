import Anthropic from "@anthropic-ai/sdk";
import { ResumeAnalysis, CVSection } from "@/types/resume";
import { createClient } from "@/utils/supabase/server";

export const runtime = "nodejs";

interface RewriteRequest {
  analysis: ResumeAnalysis;
  cvSections: CVSection[];
}

function buildPrompt(req: RewriteRequest): string {
  const feedbackItems = [
    ...req.analysis.feedback.action,
    ...req.analysis.feedback.specifics,
    ...req.analysis.feedback.overusage,
    ...req.analysis.feedback.avoided,
  ];

  return `You are an expert resume editor. Rewrite the CV sections below to address the issues identified in the feedback, applying the suggested improvements.

CRITICAL RULES:
1. Return ONLY valid JSON. No markdown, no code fences, no explanation.
2. Preserve every bullet's "id" exactly — the frontend depends on these IDs to render.
3. You may rewrite "text", "heading", "subheading", and other content fields.
4. Do NOT add new bullets or remove existing ones — keep the same count and order.
5. Keep the same section structure ("type" and "id" of each section).
6. Set "highlighted": false on bullets you've fixed (since they no longer have the issue).

EDITING GUIDANCE:
- Replace weak verbs (was/were responsible, worked on) with strong action verbs (Architected, Spearheaded, Led, Drove, Shipped).
- Add concrete metrics where possible — revenue, percentages, team sizes, timelines. If the original lacked numbers, infer reasonable estimates from context (don't invent absurd numbers).
- Remove clichés (results-driven, team player, passionate) and replace with concrete evidence.
- Apply the keyword suggestions from improvements (e.g. "OKR", "PLG", "stakeholder alignment") naturally.
- Tighten verbose phrasing while keeping all key information.
- Preserve the candidate's voice and seniority level.

Return this exact JSON shape:
{
  "cvSections": [CVSection, ...]
}

CVSection shape (same as input):
{ "id": string, "title": string, "type": "header"|"summary"|"experience"|"skills"|"education", "content": CVSectionContent }
CVSectionContent: { "heading": string, "subheading"?: string, "text"?: string, "company"?: string, "location"?: string, "date"?: string, "bullets"?: [{ "id": string, "text": string, "highlighted"?: boolean }] }

FEEDBACK TO ADDRESS:
${feedbackItems.map((f, i) => `${i + 1}. [${f.severity}] ${f.text}${f.quote ? " (re: \"" + f.quote + "\")" : ""}`).join("\n")}

IMPROVEMENTS TO APPLY (ranked):
${req.analysis.improvements.map((imp) => `${imp.rank}. [${imp.category}, ${imp.impact}] ${imp.suggestion}`).join("\n")}

CURRENT CV SECTIONS:
${JSON.stringify(req.cvSections, null, 2)}`;
}

function enforceIntegrity(
  original: CVSection[],
  rewritten: CVSection[]
): CVSection[] {
  // Build a map of original bullet IDs by section id, to verify nothing got renamed/dropped
  const originalIds = new Map<string, Set<string>>();
  for (const section of original) {
    if (section.content.bullets) {
      originalIds.set(
        section.id,
        new Set(section.content.bullets.map((b) => b.id))
      );
    }
  }

  // Re-attach any missing bullet IDs by zipping with original order (defensive)
  const result: CVSection[] = rewritten.map((section) => {
    const originalSection = original.find((s) => s.id === section.id);
    if (!section.content.bullets || !originalSection?.content.bullets) {
      return section;
    }
    // Zip rewritten bullets with original IDs in order — guarantees IDs match
    const zipped = originalSection.content.bullets.map((origBullet, i) => {
      const rewrittenBullet = section.content.bullets?.[i];
      return {
        id: origBullet.id, // ALWAYS use the original ID
        text: rewrittenBullet?.text ?? origBullet.text,
        highlighted: false, // After rewrite, no bullets are flagged
      };
    });
    return {
      ...section,
      content: { ...section.content, bullets: zipped },
    };
  });

  return result;
}

export async function POST(request: Request): Promise<Response> {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const client = new Anthropic();
  try {
    const body = (await request.json()) as RewriteRequest;
    if (!body?.analysis || !Array.isArray(body?.cvSections)) {
      return Response.json({ error: "Missing analysis or cvSections" }, { status: 400 });
    }

    const message = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 4096,
      messages: [{ role: "user", content: buildPrompt(body) }],
    });

    const textBlock = message.content.find((b) => b.type === "text");
    if (!textBlock || textBlock.type !== "text") {
      return Response.json({ error: "Unexpected AI response" }, { status: 502 });
    }

    let result: { cvSections: CVSection[] };
    try {
      result = JSON.parse(textBlock.text);
    } catch {
      return Response.json({ error: "AI returned malformed JSON" }, { status: 502 });
    }

    if (!Array.isArray(result?.cvSections)) {
      return Response.json({ error: "AI response missing cvSections" }, { status: 502 });
    }

    const cleaned = enforceIntegrity(body.cvSections, result.cvSections);
    return Response.json({ cvSections: cleaned });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    console.error("[/api/rewrite]", msg);
    return Response.json({ error: msg }, { status: 500 });
  }
}
