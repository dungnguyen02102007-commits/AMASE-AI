// Dynamically imported — only loaded when user clicks Download Improved.
// @react-pdf/renderer uses pdfkit/fontkit which reference Node built-ins (fs, path, stream).
// next.config.js stubs those out for the browser bundle.
import React from "react";
import { Document, Page, View, Text, StyleSheet, pdf } from "@react-pdf/renderer";
import type { CVSection, CVSectionContent } from "@/types/resume";

const styles = StyleSheet.create({
  page: {
    fontFamily: "Helvetica",
    fontSize: 10,
    paddingTop: 44,
    paddingBottom: 44,
    paddingHorizontal: 52,
    color: "#1e293b",
  },

  // ── Header ────────────────────────────────────────────────────────────
  header: {
    alignItems: "center",
    paddingBottom: 12,
    marginBottom: 14,
    borderBottomWidth: 1.5,
    borderBottomColor: "#1e293b",
  },
  headerName: {
    fontSize: 20,
    fontFamily: "Helvetica-Bold",
    color: "#0f172a",
  },
  headerSub: {
    fontSize: 10,
    color: "#64748b",
    marginTop: 3,
  },
  headerContact: {
    fontSize: 9,
    fontFamily: "Courier",
    color: "#94a3b8",
    marginTop: 3,
  },

  // ── Section wrapper ───────────────────────────────────────────────────
  section: {
    marginBottom: 14,
  },
  sectionTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  sectionTitle: {
    fontSize: 7.5,
    fontFamily: "Helvetica-Bold",
    color: "#334155",
    letterSpacing: 1.5,
    textTransform: "uppercase",
    marginRight: 6,
  },
  sectionRule: {
    flex: 1,
    height: 1.2,
    backgroundColor: "#1e293b",
  },

  // ── Experience ────────────────────────────────────────────────────────
  expRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "baseline",
  },
  expRole: {
    flex: 1,
    fontSize: 11,
    fontFamily: "Helvetica-Bold",
    color: "#1e293b",
  },
  expDate: {
    flexShrink: 0,
    fontSize: 9,
    fontFamily: "Courier",
    color: "#94a3b8",
  },
  expCompany: {
    fontSize: 10,
    fontFamily: "Helvetica-Oblique",
    color: "#64748b",
    marginTop: 2,
  },
  bullets: {
    marginTop: 5,
    marginLeft: 6,
  },
  bulletRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 3,
  },
  bulletDot: {
    width: 3.5,
    height: 3.5,
    borderRadius: 2,
    backgroundColor: "#94a3b8",
    marginTop: 3.5,
    marginRight: 6,
    flexShrink: 0,
  },
  bulletText: {
    flex: 1,
    fontSize: 10,
    color: "#475569",
    lineHeight: 1.45,
  },

  // ── Summary / Skills (plain text) ─────────────────────────────────────
  textBlock: {
    fontSize: 10,
    color: "#475569",
    lineHeight: 1.5,
  },

  // ── Education ─────────────────────────────────────────────────────────
  eduRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "baseline",
  },
  eduDegree: {
    flex: 1,
    fontSize: 11,
    fontFamily: "Helvetica-Bold",
    color: "#1e293b",
  },
  eduInstitution: {
    fontSize: 10,
    fontFamily: "Helvetica-Oblique",
    color: "#64748b",
    marginTop: 2,
  },
  eduNote: {
    fontSize: 9,
    color: "#94a3b8",
    marginTop: 2,
  },
});

// ── PDF sub-components ───────────────────────────────────────────────────

function PDFHeader({ content }: { content: CVSectionContent }) {
  return (
    <View style={styles.header}>
      <Text style={styles.headerName}>{content.heading}</Text>
      {content.subheading ? <Text style={styles.headerSub}>{content.subheading}</Text> : null}
      {content.text ? <Text style={styles.headerContact}>{content.text}</Text> : null}
    </View>
  );
}

function PDFExperience({ content }: { content: CVSectionContent }) {
  return (
    <View>
      <View style={styles.expRow}>
        <Text style={styles.expRole}>{content.heading}</Text>
        {content.date ? <Text style={styles.expDate}>{content.date}</Text> : null}
      </View>
      {(content.company || content.location) ? (
        <Text style={styles.expCompany}>
          {[content.company, content.location].filter(Boolean).join(" · ")}
        </Text>
      ) : null}
      {content.subheading && !content.company ? (
        <Text style={styles.expCompany}>{content.subheading}</Text>
      ) : null}
      {content.bullets && content.bullets.length > 0 ? (
        <View style={styles.bullets}>
          {content.bullets.map((b) => (
            <View key={b.id} style={styles.bulletRow}>
              <View style={styles.bulletDot} />
              <Text style={styles.bulletText}>{b.text}</Text>
            </View>
          ))}
        </View>
      ) : null}
    </View>
  );
}

function PDFTextBlock({ content }: { content: CVSectionContent }) {
  return <Text style={styles.textBlock}>{content.text ?? content.heading}</Text>;
}

function PDFEducation({ content }: { content: CVSectionContent }) {
  return (
    <View>
      <View style={styles.eduRow}>
        <Text style={styles.eduDegree}>{content.heading}</Text>
        {content.date ? <Text style={styles.expDate}>{content.date}</Text> : null}
      </View>
      {content.subheading ? (
        <Text style={styles.eduInstitution}>{content.subheading}</Text>
      ) : null}
      {content.text ? <Text style={styles.eduNote}>{content.text}</Text> : null}
    </View>
  );
}

function PDFSection({ section }: { section: CVSection }) {
  const { type, title, content } = section;
  if (type === "header") return <PDFHeader content={content} />;
  return (
    <View style={styles.section}>
      <View style={styles.sectionTitleRow}>
        <Text style={styles.sectionTitle}>{title}</Text>
        <View style={styles.sectionRule} />
      </View>
      {type === "experience" && <PDFExperience content={content} />}
      {(type === "summary" || type === "skills") && <PDFTextBlock content={content} />}
      {type === "education" && <PDFEducation content={content} />}
    </View>
  );
}

function ResumePDF({ sections }: { sections: CVSection[] }) {
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        {sections.map((section) => (
          <PDFSection key={section.id} section={section} />
        ))}
      </Page>
    </Document>
  );
}

// ── Public API ────────────────────────────────────────────────────────────

export async function downloadResumePdf(
  sections: CVSection[],
  candidateName: string
): Promise<void> {
  const blob = await pdf(<ResumePDF sections={sections} />).toBlob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const date = new Date().toISOString().slice(0, 10);
  const safeName = (candidateName.trim() || "resume").replace(/\s+/g, "_");
  a.download = `${safeName}_resume_${date}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
