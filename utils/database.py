"""SQLite persistence layer for blood cell analysis reports.

Stores one row per analysed image, including detection counts,
parasitemia and the paths to the generated PDF / CSV reports.
The database location is fixed at ``database/reports.db`` and must
not be changed.
"""

import os
import sqlite3
from datetime import datetime

DB_PATH = "database/reports.db"


# --------------------------------------------------------------------------- #
# Connection helpers
# --------------------------------------------------------------------------- #
def get_connection():
    """Return a SQLite connection with dict-style row access.

    Using ``sqlite3.Row`` lets callers reference columns by name
    (``row["pdf_path"]``) instead of fragile positional indexes,
    which keeps the templates stable even when new columns are added.
    """

    # Ensure the parent directory exists without changing its location.
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# --------------------------------------------------------------------------- #
# Schema management
# --------------------------------------------------------------------------- #
def initialize_database():
    """Create the reports table if missing and apply lightweight migrations."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,

            image_name      TEXT,
            output_image    TEXT,

            rbc_count       INTEGER,
            wbc_count       INTEGER,
            platelet_count  INTEGER,
            parasite_count  INTEGER,

            parasitemia     REAL,

            pdf_path        TEXT,
            csv_path        TEXT,

            created_at      TEXT
        )
    """)

    # Migration: add csv_path to databases created before this column existed.
    existing_columns = {
        row["name"] for row in cursor.execute("PRAGMA table_info(reports)")
    }

    if "csv_path" not in existing_columns:
        cursor.execute("ALTER TABLE reports ADD COLUMN csv_path TEXT")

    conn.commit()
    conn.close()


# --------------------------------------------------------------------------- #
# Write operations
# --------------------------------------------------------------------------- #
def save_report(
        image_name,
        output_image,
        rbc_count,
        wbc_count,
        platelet_count,
        parasite_count,
        parasitemia,
        pdf_path,
        csv_path
):
    """Persist a single analysis result and return its new row id."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports(
            image_name,
            output_image,
            rbc_count,
            wbc_count,
            platelet_count,
            parasite_count,
            parasitemia,
            pdf_path,
            csv_path,
            created_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?)
    """,
    (
        image_name,
        output_image,
        rbc_count,
        wbc_count,
        platelet_count,
        parasite_count,
        parasitemia,
        pdf_path,
        csv_path,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    report_id = cursor.lastrowid
    conn.close()

    return report_id


def delete_report(report_id):
    """Delete a report row by id. Returns True if a row was removed."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))

    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


# --------------------------------------------------------------------------- #
# Read operations
# --------------------------------------------------------------------------- #
def get_all_reports():
    """Return every report (newest first) as a list of dict-like rows."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports ORDER BY id DESC")

    data = cursor.fetchall()

    conn.close()

    return data


def get_report_by_id(report_id):
    """Return a single report row, or ``None`` if it does not exist."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))

    row = cursor.fetchone()

    conn.close()

    return row


def get_summary_stats():
    """Return aggregate totals used by the reports dashboard cards."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*)                         AS total_reports,
            COALESCE(SUM(rbc_count), 0)      AS total_rbc,
            COALESCE(SUM(wbc_count), 0)      AS total_wbc,
            COALESCE(SUM(platelet_count), 0) AS total_platelets,
            COALESCE(SUM(parasite_count), 0) AS total_parasites
        FROM reports
    """)

    row = cursor.fetchone()

    conn.close()

    return {
        "total_reports": row["total_reports"],
        "total_rbc": row["total_rbc"],
        "total_wbc": row["total_wbc"],
        "total_platelets": row["total_platelets"],
        "total_parasites": row["total_parasites"],
    }
