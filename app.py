"""Flask application entry point.

AI-Powered Blood Cell Detection & Parasitemia Analysis System.
Routes:
    /                  Landing page with upload form
    /detect            Run YOLO detection on an uploaded image
    /reports           Analysis history dashboard
    /download/pdf/...  Download a generated PDF report
    /download/csv/...  Download a generated CSV report
    /delete/<id>       Delete a stored report
    /sample/<kind>     Analyze a curated demo image (random/healthy/malaria/advanced)
    /download-sample-dataset  Download the curated demo dataset as a ZIP
"""

import os
import shutil
import zipfile

import random
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    send_file,
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

# Curated demo dataset (healthy / malaria / advanced).
SAMPLE_DIR = "sample_data"
SAMPLE_CATEGORIES = ("healthy", "malaria", "advanced")
SAMPLE_ZIP_PATH = "blood_cell_sample_dataset.zip"

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
# Shared analysis pipeline
# --------------------------------------------------------------------------- #
def process_image(image_path, source="Uploaded Image"):
    """Run the full analysis pipeline on an image and render the result page.

    This is the single source of truth for the workflow used by BOTH the
    upload route and every sample route:
        detection -> counting -> parasitemia -> reports -> database -> result.

    ``image_path`` must already live inside ``static/uploads`` so the result
    template can render the original image alongside the annotated output.
    """

    filename = os.path.basename(image_path)

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
        source=source,
    )


def _pick_sample(category):
    """Return a random image Path from a sample category (or None if empty)."""
    folder = Path(SAMPLE_DIR) / category
    candidates = [
        p for p in folder.glob("*")
        if p.suffix.lower().lstrip(".") in ALLOWED_EXTENSIONS
    ]
    return random.choice(candidates) if candidates else None


def run_sample(category, source):
    """Stage a random sample image into uploads and run the shared pipeline."""
    sample = _pick_sample(category)

    if sample is None:
        flash(f"No sample images available in '{category}'.", "error")
        return redirect(url_for("home"))

    # Copy into the uploads folder so the workflow is identical to an upload.
    dest_path = os.path.join(UPLOAD_FOLDER, secure_filename(sample.name))
    shutil.copyfile(sample, dest_path)

    return process_image(dest_path, source=source)


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

    # Delegate to the shared pipeline (same path used by sample routes).
    return process_image(image_path, source="Uploaded Image")


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
# Sample dataset (all reuse the shared process_image pipeline)
# --------------------------------------------------------------------------- #
@app.route("/sample/random")
def random_sample():
    """Analyze a random image pooled from every sample category."""
    pool = [
        p
        for category in SAMPLE_CATEGORIES
        for p in (Path(SAMPLE_DIR) / category).glob("*")
        if p.suffix.lower().lstrip(".") in ALLOWED_EXTENSIONS
    ]

    if not pool:
        flash("No sample images are available.", "error")
        return redirect(url_for("home"))

    sample = random.choice(pool)
    dest_path = os.path.join(UPLOAD_FOLDER, secure_filename(sample.name))
    shutil.copyfile(sample, dest_path)

    return process_image(dest_path, source="Random Sample")


@app.route("/sample/healthy")
def healthy_sample():
    return run_sample("healthy", source="Healthy Sample")


@app.route("/sample/malaria")
def malaria_sample():
    return run_sample("malaria", source="Malaria Sample")


@app.route("/sample/advanced")
def advanced_sample():
    return run_sample("advanced", source="Advanced Sample")


# --------------------------------------------------------------------------- #
# Dataset download
# --------------------------------------------------------------------------- #
def _build_sample_zip():
    """(Re)build the downloadable archive from the current sample_data folder."""
    with zipfile.ZipFile(SAMPLE_ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, _dirs, files in os.walk(SAMPLE_DIR):
            for name in files:
                full_path = os.path.join(root, name)
                # Store paths relative to the project root -> "sample_data/...".
                archive.write(full_path, os.path.relpath(full_path, "."))
    return SAMPLE_ZIP_PATH


@app.route("/download-sample-dataset")
def download_sample_dataset():
    """Serve the curated sample dataset as a single ZIP download."""
    if not os.path.isdir(SAMPLE_DIR):
        abort(404)

    # Build the archive on demand if it does not already exist.
    if not os.path.isfile(SAMPLE_ZIP_PATH):
        _build_sample_zip()

    return send_file(
        SAMPLE_ZIP_PATH,
        as_attachment=True,
        download_name="blood_cell_sample_dataset.zip",
    )


# --------------------------------------------------------------------------- #
# Error handling
# --------------------------------------------------------------------------- #
@app.errorhandler(413)
def file_too_large(_error):
    flash("That file is too large. Maximum upload size is 16 MB.", "error")
    return redirect(url_for("home"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)