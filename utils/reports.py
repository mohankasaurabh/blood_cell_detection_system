# utils/reports.py
"""Report generation utilities (PDF + CSV).

Both generators write into the fixed ``reports/pdf`` and ``reports/csv``
directories and return the relative path of the file they created so the
caller can persist it in the database and expose a download link.
"""

import os
import csv
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Spacer,
    Paragraph,
    Table,
    TableStyle,
)


PDF_DIR = "reports/pdf"
CSV_DIR = "reports/csv"


os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)


# Brand palette shared with the web UI for a consistent look.
BRAND_PRIMARY = colors.HexColor("#2563eb")
BRAND_DARK = colors.HexColor("#0f172a")
BRAND_DANGER = colors.HexColor("#ef4444")
BRAND_SUCCESS = colors.HexColor("#10b981")
ROW_ALT = colors.HexColor("#f1f5f9")


def _timestamp():
    """Return a filesystem-safe timestamp used for unique report names."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


# --------------------------------------------------------------------------- #
# PDF report
# --------------------------------------------------------------------------- #
def generate_pdf_report(
        image_name,
        rbc_count,
        wbc_count,
        platelet_count,
        parasite_count,
        parasitemia
):
    """Render a professional one-page PDF report and return its path."""

    pdf_name = f"report_{_timestamp()}.pdf"
    pdf_path = os.path.join(PDF_DIR, pdf_name)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        topMargin=24 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        textColor=BRAND_DARK,
        fontSize=22,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        textColor=colors.HexColor("#64748b"),
        fontSize=10,
    )

    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontSize=10,
        leading=16,
    )

    parasites_found = parasite_count > 0
    status_text = (
        "Parasites Detected" if parasites_found else "No Parasites Detected"
    )
    status_color = BRAND_DANGER if parasites_found else BRAND_SUCCESS

    content = []

    # --- Header -------------------------------------------------------------
    content.append(Paragraph("Blood Cell Analysis Report", title_style))
    content.append(
        Paragraph(
            "AI-Powered Blood Cell Detection &amp; Parasitemia Analysis "
            "(YOLO11m)",
            subtitle_style,
        )
    )
    content.append(Spacer(1, 16))

    # --- Metadata -----------------------------------------------------------
    content.append(Paragraph(f"<b>Image:</b> {image_name}", meta_style))
    content.append(
        Paragraph(
            f"<b>Generated:</b> "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            meta_style,
        )
    )
    content.append(Spacer(1, 18))

    # --- Detection summary table -------------------------------------------
    table_data = [
        ["Metric", "Value"],
        ["RBC Count", str(rbc_count)],
        ["WBC Count", str(wbc_count)],
        ["Platelet Count", str(platelet_count)],
        ["Parasite Count", str(parasite_count)],
        ["Parasitemia", f"{parasitemia} %"],
        ["Status", status_text],
    ]

    table = Table(table_data, colWidths=[90 * mm, 80 * mm])
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        # Body
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("TEXTCOLOR", (0, 1), (0, -1), BRAND_DARK),
        # Highlight the status value
        ("TEXTCOLOR", (1, -1), (1, -1), status_color),
        ("FONTNAME", (1, -1), (1, -1), "Helvetica-Bold"),
        # Layout
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))

    content.append(table)
    content.append(Spacer(1, 24))

    # --- Footer / disclaimer ------------------------------------------------
    content.append(
        Paragraph(
            "<i>This report was generated automatically by an AI model and is "
            "intended for research and demonstration purposes only. It is not "
            "a substitute for professional medical diagnosis.</i>",
            subtitle_style,
        )
    )

    doc.build(content)

    return pdf_path


# --------------------------------------------------------------------------- #
# CSV report
# --------------------------------------------------------------------------- #
def generate_csv_report(
        image_name,
        rbc_count,
        wbc_count,
        platelet_count,
        parasite_count,
        parasitemia
):
    """Write a single-row CSV summary and return its path."""

    csv_name = f"report_{_timestamp()}.csv"
    csv_path = os.path.join(CSV_DIR, csv_name)

    status = "Parasites Detected" if parasite_count > 0 else "No Parasites Detected"

    with open(csv_path, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Image",
            "RBC",
            "WBC",
            "Platelet",
            "Parasite",
            "Parasitemia (%)",
            "Status",
            "Generated",
        ])

        writer.writerow([
            image_name,
            rbc_count,
            wbc_count,
            platelet_count,
            parasite_count,
            parasitemia,
            status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])

    return csv_path
