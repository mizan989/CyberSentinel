"""
CyberSentinel - PDF Report
-------------------------------
Builds the PDF report described in the blueprint's "Report Layout"
section, using ReportLab's Platypus layout engine.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

ACCENT = colors.HexColor("#00A86B")
DARK = colors.HexColor("#0D1117")
LIGHT_GREY = colors.HexColor("#E5E5E5")

SEVERITY_COLORS = {
    "Critical": "#D32F2F",
    "High": "#F57C00",
    "Medium": "#FBC02D",
    "Low": "#388E3C",
    "Informational": "#1976D2",
}


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CSTitle",
            fontSize=22,
            leading=26,
            textColor=DARK,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CSSubtitle",
            fontSize=11,
            textColor=colors.grey,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CSSection",
            fontSize=13,
            textColor=ACCENT,
            spaceBefore=14,
            spaceAfter=6,
        )
    )
    return styles


def generate_pdf_report(scan_data, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        title=f"CyberSentinel Report - {scan_data.get('target')}",
    )
    styles = _styles()
    story = []

    # Header
    story.append(Paragraph("CyberSentinel Report", styles["CSTitle"]))
    story.append(
        Paragraph(
            "Automated Vulnerability Scanner &amp; Reporting Dashboard",
            styles["CSSubtitle"],
        )
    )
    story.append(HRFlowable(width="100%", color=ACCENT, thickness=1.2))

    # General information
    story.append(Paragraph("General Information", styles["CSSection"]))
    general_rows = [
        ["Target", scan_data.get("target", "-")],
        ["Hostname", scan_data.get("hostname", scan_data.get("target", "-"))],
        ["Scan Type", scan_data.get("scan_type", "-")],
        ["Scan Date", scan_data.get("started_at", "-")],
        ["Duration", f"{scan_data.get('duration_seconds', 0):.1f}s"
                       if scan_data.get("duration_seconds") else "-"],
    ]
    story.append(_kv_table(general_rows))

    # OS
    story.append(Paragraph("Operating System", styles["CSSection"]))
    story.append(Paragraph(scan_data.get("os_guess") or "Not determined", styles["Normal"]))

    # Open ports / services
    story.append(Paragraph("Open Ports &amp; Services", styles["CSSection"]))
    services = scan_data.get("services", [])
    if services:
        data = [["Port", "Protocol", "Service", "Version", "State"]]
        for s in services:
            data.append(
                [
                    str(s.get("port", "-")),
                    s.get("protocol", "-"),
                    s.get("service", "-"),
                    s.get("version", "-"),
                    s.get("state", "-"),
                ]
            )
        story.append(_data_table(data, col_widths=[45, 55, 90, 190, 60]))
    else:
        story.append(Paragraph("No open ports/services detected.", styles["Normal"]))

    # Vulnerabilities
    story.append(Paragraph("Detected Vulnerabilities", styles["CSSection"]))
    vulns = scan_data.get("vulnerabilities", [])
    if vulns:
        for v in vulns:
            sev = v.get("severity", "Informational")
            color = SEVERITY_COLORS.get(sev, "#666666")
            header = f'<font color="{color}"><b>[{sev}]</b></font> ' \
                      f'{v.get("service", "")} {v.get("version", "")} ' \
                      f'&mdash; {v.get("cve", "N/A")}'
            story.append(Paragraph(header, styles["Normal"]))
            story.append(Paragraph(v.get("description", ""), styles["Normal"]))
            story.append(
                Paragraph(f"<i>Recommendation:</i> {v.get('recommendation', '')}",
                           styles["Normal"])
            )
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("No vulnerabilities matched in the offline database.",
                                 styles["Normal"]))

    # Risk score
    story.append(Paragraph("Risk Score", styles["CSSection"]))
    story.append(
        Paragraph(
            f"<b>{scan_data.get('risk_score', 0)}/100 &mdash; "
            f"{scan_data.get('risk_level', 'Informational')}</b>",
            styles["Normal"],
        )
    )

    # Recommendations
    story.append(Paragraph("Recommendations", styles["CSSection"]))
    story.append(
        Paragraph(
            "This report uses a small offline CVE lookup table for "
            "demonstration purposes and simple substring version "
            "matching. It is not a substitute for a production-grade "
            "vulnerability management tool. Always confirm exposure "
            "manually before remediating.",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=colors.lightgrey, thickness=0.5))
    story.append(
        Paragraph(
            "CyberSentinel by Md Mizan— for authorized demonstration "
            "targets only.",
            styles["CSSubtitle"],
        )
    )

    doc.build(story)
    return output_path


def _kv_table(rows):
    t = Table(rows, colWidths=[110, 320])
    t.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.whitesmoke),
            ]
        )
    )
    return t


def _data_table(data, col_widths):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
            ]
        )
    )
    return t
