export type Severity = "high" | "medium" | "low";
export type ScoreGrade = "needs-work" | "good" | "excellent";
export type ImpactLevel = "high" | "medium" | "low";

export interface ScoreBreakdown {
  impact: number;
  presentation: number;
  competencies: number;
}

export interface FeedbackItem {
  id: string;
  text: string;
  quote?: string;
  severity: Severity;
  cvLineId?: string;
}

export interface FeedbackSection {
  key: "action" | "specifics" | "overusage" | "avoided";
  label: string;
  description: string;
  items: FeedbackItem[];
  color: string;
  bgColor: string;
}

export interface Feedback {
  action: FeedbackItem[];
  specifics: FeedbackItem[];
  overusage: FeedbackItem[];
  avoided: FeedbackItem[];
}

export interface Improvement {
  id: string;
  rank: number;
  category: string;
  suggestion: string;
  impact: ImpactLevel;
  pointsGain: string;
}

export interface AIInsight {
  id: string;
  title: string;
  detail: string;
  severity: Severity;
  feedbackId?: string;
  isQuickWin?: boolean;
}

export interface ResumeAnalysis {
  candidateName: string;
  targetRole: string;
  analysisDate: string;
  score: number;
  maxScore: number;
  percentile: number;
  issueCount: number;
  scorePotential: { low: number; high: number };
  breakdown: ScoreBreakdown;
  feedback: Feedback;
  improvements: Improvement[];
  insights: AIInsight[];
}

export interface CVLine {
  id: string;
  text: string;
  feedbackId?: string;
  isHighlighted?: boolean;
}

export interface CVBullet {
  id: string;
  line: CVLine;
}

export interface CVJob {
  id: string;
  role: string;
  company: string;
  location: string;
  date: string;
  bullets: CVBullet[];
}

export interface CVBulletContent {
  id: string;
  text: string;
  highlighted?: boolean;
}

export interface CVSectionContent {
  heading: string;
  subheading?: string;
  text?: string;
  company?: string;
  location?: string;
  date?: string;
  bullets?: CVBulletContent[];
}

export interface CVSection {
  id: string;
  title: string;
  type: "header" | "summary" | "experience" | "skills" | "education";
  content: CVSectionContent;
}

export interface FeedbackCVMapping {
  [feedbackId: string]: {
    cvLineId: string;
    sectionId: string;
  } | null;
}

export type UploadStatus = "idle" | "uploading" | "parsing" | "done" | "error";

export interface UploadState {
  status: UploadStatus;
  fileName: string | null;
  progress: number;
  error: string | null;
}

export interface HistoryEntry {
  id: string;
  fileName: string;
  createdAt: string; // ISO timestamp
  analysis: ResumeAnalysis;
  cvSections: CVSection[];
}

export interface CompareSlot {
  label: string;
  analysis: ResumeAnalysis | null;
  fileName: string | null;
}

export interface CategoryComparison {
  category: string;
  scoreA: number;
  scoreB: number;
  winner: "a" | "b" | "tie";
}