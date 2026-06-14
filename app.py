"""Flask application entry point.

AI-Powered Blood Cell Detection & Parasitemia Analysis System.
Routes:
    /                  Landing page with upload form
    /detect            Run YOLO detection on an uploaded image
    /reports           Analysis history dashboard
    /download/pdf/...  Download a generated PDF report
    /download/csv/...  Download a generated CSV report
    /delete/<id>       Delete a stored report
"""

import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    send_from_directory,
)

from werkzeug.utils import secure_filename

from utils.detector import run_detection
from utils.counter import count_cells
from utils.calculator import calculate_parasitemia
from utils.reports import (
    generate_pdf_report,
    generate_csv_report,
    PDF_DIR,
    CSV_DIR,
)

from utils.database import (
    initialize_database,
    save_report,
    get_all_reports,
    get_report_by_id,
    delete_report,
    get_summary_stats,
)


app = Flask(__name__)

# Secret key is required for flash() notifications.
app.secret_key = os.environ.get("SECRET_KEY", "blood-cell-detection-dev-key")

UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/outputs"

# Limit uploads to 16 MB and restrict to common image formats.
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


initialize_database()


def allowed_file(filename):
    """Return True if the filename has a permitted image extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/detect", methods=["POST"])
def detect():
    """Validate the upload, run detection, persist and render the result."""

    if "image" not in request.files:
        flash("No image was uploaded.", "error")
        return redirect(url_for("home"))

    file = request.files["image"]

    if file.filename == "":
        flash("Please choose an image before running detection.", "error")
        return redirect(url_for("home"))

    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload a JPG, JPEG or PNG.", "error")
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(image_path)

    # --- Inference & analysis ----------------------------------------------
    detections, output_path = run_detection(image_path)
    counts, confidences = count_cells(detections)
    parasitemia = calculate_parasitemia(counts["Parasite"], counts["RBC"])

    # --- Reports ------------------------------------------------------------
    pdf_path = generate_pdf_report(
        filename,
        counts["RBC"],
        counts["WBC"],
        counts["Platelet"],
        counts["Parasite"],
        parasitemia,
    )

    csv_path = generate_csv_report(
        filename,
        counts["RBC"],
        counts["WBC"],
        counts["Platelet"],
        counts["Parasite"],
        parasitemia,
    )

    # --- Persist ------------------------------------------------------------
    save_report(
        filename,
        os.path.basename(output_path),
        counts["RBC"],
        counts["WBC"],
        counts["Platelet"],
        counts["Parasite"],
        parasitemia,
        pdf_path,
        csv_path,
    )

    return render_template(
        "result.html",
        image=filename,
        output=os.path.basename(output_path),
        counts=counts,
        confidences=confidences,
        parasitemia=parasitemia,
        pdf_file=os.path.basename(pdf_path),
        csv_file=os.path.basename(csv_path),
    )


@app.route("/reports")
def reports():
    report_data = get_all_reports()
    stats = get_summary_stats()

    return render_template(
        "reports.html",
        reports=report_data,
        stats=stats,
    )


# --------------------------------------------------------------------------- #
# Downloads
# --------------------------------------------------------------------------- #
@app.route("/download/pdf/<path:filename>")
def download_pdf(filename):
    """Serve a generated PDF report as a download attachment."""
    safe_name = secure_filename(filename)
    file_path = os.path.join(PDF_DIR, safe_name)

    if not os.path.isfile(file_path):
        abort(404)

    return send_from_directory(PDF_DIR, safe_name, as_attachment=True)


@app.route("/download/csv/<path:filename>")
def download_csv(filename):
    """Serve a generated CSV report as a download attachment."""
    safe_name = secure_filename(filename)
    file_path = os.path.join(CSV_DIR, safe_name)

    if not os.path.isfile(file_path):
        abort(404)

    return send_from_directory(CSV_DIR, safe_name, as_attachment=True)


# --------------------------------------------------------------------------- #
# Mutations
# --------------------------------------------------------------------------- #
@app.route("/delete/<int:report_id>", methods=["POST"])
def remove_report(report_id):
    """Delete a stored report and its associated PDF / CSV files."""
    report = get_report_by_id(report_id)

    if report is None:
        flash("Report not found.", "error")
        return redirect(url_for("reports"))

    # Best-effort cleanup of the generated files on disk.
    for path_key in ("pdf_path", "csv_path"):
        file_path = report[path_key]
        if file_path and os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    delete_report(report_id)
    flash("Report deleted successfully.", "success")
    return redirect(url_for("reports"))


# --------------------------------------------------------------------------- #
# Error handling
# --------------------------------------------------------------------------- #
@app.errorhandler(413)
def file_too_large(_error):
    flash("That file is too large. Maximum upload size is 16 MB.", "error")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
