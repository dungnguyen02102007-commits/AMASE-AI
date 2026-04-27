import { ResumeAnalysis, FeedbackCVMapping, CVSection } from "@/types/resume";

export const mockAnalysis: ResumeAnalysis = {
  candidateName: "Alexandra Chen",
  targetRole: "Senior Product Manager",
  analysisDate: "April 22, 2026",
  score: 38,
  maxScore: 100,
  percentile: 12,
  issueCount: 14,
  scorePotential: { low: 72, high: 80 },
  breakdown: { impact: 22, presentation: 11, competencies: 5 },
  insights: [
    { id: "i1", title: "Weak action verbs", detail: "4 instances", severity: "high", feedbackId: "a1" },
    { id: "i2", title: "Missing metrics", detail: "3 bullets unquantified", severity: "high", feedbackId: "s1" },
    { id: "i3", title: '"Responsible for" x4', detail: "Overused phrase", severity: "medium", feedbackId: "o1" },
    { id: "i4", title: "Clichés detected", detail: "3 buzzwords to remove", severity: "medium", feedbackId: "av1" },
    { id: "i5", title: "Add OKR keyword", detail: "+3-5 pts", severity: "low", isQuickWin: true },
    { id: "i6", title: "Reorder Skills section", detail: "+2-4 pts", severity: "low", isQuickWin: true },
  ],
  feedback: {
    action: [
      { id: "a1", text: "Use stronger action verbs to begin bullet points", quote: "Led cross-functional teams...", severity: "high", cvLineId: "cvl-a1" },
      { id: "a2", text: "Replace passive constructions with active voice", quote: "Was responsible for managing...", severity: "high", cvLineId: "cvl-a2" },
      { id: "a3", text: "Use dynamic verbs: Architected, Spearheaded, Pioneered", severity: "medium", cvLineId: "cvl-a3" },
    ],
    specifics: [
      { id: "s1", text: "Add quantifiable metrics to achievements", quote: "Improved user engagement significantly", severity: "high", cvLineId: "cvl-s1" },
      { id: "s2", text: "Include specific timeframes for major projects", severity: "medium", cvLineId: "cvl-s2" },
      { id: "s3", text: "Specify team sizes in leadership descriptions", severity: "medium", cvLineId: "cvl-s3" },
    ],
    overusage: [
      { id: "o1", text: '"Responsible for" used 4x - replace with direct verbs', severity: "high", cvLineId: "cvl-o1" },
      { id: "o2", text: '"Worked with" appears 3x - be specific about role', severity: "medium", cvLineId: "cvl-o2" },
      { id: "o3", text: '"Various" is vague - appears multiple times', severity: "low" },
    ],
    avoided: [
      { id: "av1", text: '"Results-driven" is a cliche - weakens profile', severity: "medium", cvLineId: "cvl-av1" },
      { id: "av2", text: '"Team player" adds no value - show via examples', severity: "medium", cvLineId: "cvl-av2" },
      { id: "av3", text: '"Passionate" - show it through achievements instead', severity: "low", cvLineId: "cvl-av3" },
    ],
  },
  improvements: [
    { id: "imp1", rank: 1, category: "Quantification", suggestion: 'Add revenue impact to product launch bullets. e.g., "Launched feature X, driving $2M ARR"', impact: "high", pointsGain: "+10-14" },
    { id: "imp2", rank: 2, category: "Keywords", suggestion: "Add 'OKR', 'Go-to-market', 'Stakeholder alignment' to pass ATS filters", impact: "high", pointsGain: "+8-12" },
    { id: "imp3", rank: 3, category: "Structure", suggestion: "Move Skills section above Work Experience to boost ATS scan speed", impact: "medium", pointsGain: "+4-6" },
    { id: "imp4", rank: 4, category: "Summary", suggestion: "Rewrite summary as a 3-line value proposition for Senior PM roles", impact: "high", pointsGain: "+8-10" },
    { id: "imp5", rank: 5, category: "Achievements", suggestion: "Add 'Key Achievements' subsection under most recent role with 2-3 wins", impact: "medium", pointsGain: "+4-6" },
    { id: "imp6", rank: 6, category: "Education", suggestion: "Include PMP, Pragmatic Marketing certifications in Education section", impact: "low", pointsGain: "+2-3" },
  ],
};

export const feedbackCVMapping: FeedbackCVMapping = {
  "a1": { cvLineId: "cvl-a1", sectionId: "cv-job1" },
  "a2": { cvLineId: "cvl-a2", sectionId: "cv-job1" },
  "a3": { cvLineId: "cvl-a3", sectionId: "cv-job2" },
  "s1": { cvLineId: "cvl-s1", sectionId: "cv-job1" },
  "s2": { cvLineId: "cvl-s2", sectionId: "cv-job2" },
  "s3": { cvLineId: "cvl-s3", sectionId: "cv-job2" },
  "o1": { cvLineId: "cvl-o1", sectionId: "cv-job2" },
  "o2": { cvLineId: "cvl-o2", sectionId: "cv-job1" },
  "o3": null,
  "av1": { cvLineId: "cvl-av1", sectionId: "cv-summary" },
  "av2": { cvLineId: "cvl-av2", sectionId: "cv-summary" },
  "av3": { cvLineId: "cvl-av3", sectionId: "cv-summary" },
};

export const mockCVSections: CVSection[] = [
  {
    id: "cv-header",
    title: "Header",
    type: "header",
    content: {
      heading: "Alexandra Chen",
      subheading: "Product Manager · San Francisco, CA",
      text: "alexandra.chen@email.com · linkedin.com/in/alexchen · (415) 555-0192",
    },
  },
  {
    id: "cv-summary",
    title: "Professional Summary",
    type: "summary",
    content: {
      heading: "Professional Summary",
      text: "Results-driven product manager with 6 years of experience working with various cross-functional teams. Passionate about building user-centric products and driving business impact. Team player with strong communication skills.",
    },
  },
  {
    id: "cv-job1",
    title: "Work Experience",
    type: "experience",
    content: {
      heading: "Senior Product Manager",
      company: "TechCorp Inc.",
      location: "San Francisco, CA",
      date: "Jan 2022 - Present",
      bullets: [
        { id: "cvl-a2", text: "Was responsible for managing the product roadmap for the core platform", highlighted: true },
        { id: "cvl-o2", text: "Worked with engineering, design, and marketing teams on various initiatives", highlighted: true },
        { id: "cvl-a1", text: "Led cross-functional teams to deliver product launches", highlighted: false },
        { id: "cvl-s1", text: "Improved user engagement significantly through feature improvements", highlighted: true },
      ],
    },
  },
  {
    id: "cv-job2",
    title: "Work Experience",
    type: "experience",
    content: {
      heading: "Product Manager",
      company: "StartupXYZ",
      location: "New York, NY",
      date: "Mar 2019 - Dec 2021",
      bullets: [
        { id: "cvl-s2", text: "Managed a large-scale migration of legacy systems to cloud infrastructure", highlighted: false },
        { id: "cvl-o1", text: "Responsible for defining product requirements and user stories", highlighted: true },
        { id: "cvl-s3", text: "Worked on go-to-market strategy for 3 product launches", highlighted: false },
        { id: "cvl-a3", text: "Led a team of developers through agile sprints", highlighted: false },
      ],
    },
  },
  {
    id: "cv-skills",
    title: "Skills",
    type: "skills",
    content: {
      heading: "Skills",
      text: "Product Strategy · Roadmap Planning · Agile/Scrum · Data Analysis · User Research · A/B Testing · SQL · Figma · JIRA · Stakeholder Management",
    },
  },
  {
    id: "cv-education",
    title: "Education",
    type: "education",
    content: {
      heading: "B.S. Computer Science",
      subheading: "University of California, Berkeley",
      date: "2013 - 2017",
    },
  },
];

