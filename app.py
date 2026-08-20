"""
CyberSentinel - Flask Application
-------------------------------
Ties together the scan engine, database, CVE matcher, risk scorer and
report generators behind a small set of routes + a JSON API.

Scans run in a background thread so the UI can poll /api/scan/<id>/status
for real-time progress without blocking the request/response cycle.
"""

import os
import threading
import time
import traceback
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file, abort

from config import Config
from database import models
from scanner import nmap_scanner, parser, vulnerability, risk, discovery
from reports.pdf import generate_pdf_report

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(Config.SCANS_DIR, exist_ok=True)
os.makedirs(Config.REPORTS_DIR, exist_ok=True)
models.init_db()

# In-memory progress tracker: scan_id -> {"stage": str, "percent": int}
# The DB holds the durable "status" (queued/running/finished/error);
# this dict just gives the frontend a friendlier live label to poll.
PROGRESS = {}
PROGRESS_LOCK = threading.Lock()

STAGES = [
    ("running", "Running Nmap", 20),
    ("parsing", "Parsing XML", 45),
    ("checking_cve", "Checking CVEs", 65),
    ("scoring", "Calculating Risk", 80),
    ("reporting", "Generating Report", 95),
    ("finished", "Finished", 100),
]


def _set_progress(scan_id, stage_key):
    label, percent = next((l, p) for k, l, p in STAGES if k == stage_key)
    with PROGRESS_LOCK:
        PROGRESS[scan_id] = {"stage": stage_key, "label": label, "percent": percent}


def _run_scan_background(scan_id, target, scan_type, custom_flags):
    start = time.time()
    try:
        models.update_scan_status(scan_id, "running")
        _set_progress(scan_id, "running")
        scanner_obj, _raw_xml = nmap_scanner.run_scan(target, scan_type, custom_flags)

        _set_progress(scan_id, "parsing")
        parsed = parser.parse_scan(scanner_obj, target)
        models.add_services(scan_id, parsed["services"])

        _set_progress(scan_id, "checking_cve")
        vulns = vulnerability.match_vulnerabilities(parsed["services"])
        models.add_vulnerabilities(scan_id, vulns)

        _set_progress(scan_id, "scoring")
        score, level = risk.calculate_risk(vulns)

        duration = time.time() - start
        models.finish_scan(scan_id, duration, score, level, parsed["os_guess"])

        _set_progress(scan_id, "reporting")
        report_data = models.full_report_data(scan_id)
        report_data["target"] = target
        report_data["hostname"] = parsed["hostname"]
        report_data["scan_type"] = scan_type
        pdf_path = os.path.join(Config.REPORTS_DIR, f"scan_{scan_id}.pdf")
        generate_pdf_report(report_data, pdf_path)

        _set_progress(scan_id, "finished")

    except nmap_scanner.TargetNotAllowedError as e:
        models.update_scan_status(scan_id, "error", str(e))
        with PROGRESS_LOCK:
            PROGRESS[scan_id] = {"stage": "error", "label": str(e), "percent": 100}
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        models.update_scan_status(scan_id, "error", str(e))
        with PROGRESS_LOCK:
            PROGRESS[scan_id] = {
                "stage": "error",
                "label": f"Scan failed: {e}",
                "percent": 100,
            }


# ---------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------

@app.route("/")
def home():
    return render_template(
        "index.html",
        stats=models.stats(),
        latest=models.list_scans(limit=5),
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/privacy")
def privacy_page():
    return render_template("privacy.html")


@app.route("/terms")
def terms_page():
    return render_template("terms.html")



@app.route("/scan", methods=["GET"])
def scan_page():
    return render_template(
        "scan.html",
        allowed_targets=Config.ALLOWED_TARGETS,
        scan_profiles=Config.SCAN_PROFILES,
        prefill_target=request.args.get("target", ""),
    )


@app.route("/discover")
def discover_page():
    return render_template("discover.html")


@app.route("/history")
def history():
    q = request.args.get("q", "").strip()
    return render_template("history.html", scans=models.list_scans(limit=100, search=q or None), q=q)


@app.route("/report/<int:scan_id>")
def report_view(scan_id):
    data = models.full_report_data(scan_id)
    if not data:
        abort(404)
    return render_template("report.html", scan=data, standalone=False)


@app.route("/report/<int:scan_id>/pdf")
def report_pdf(scan_id):
    path = os.path.join(Config.REPORTS_DIR, f"scan_{scan_id}.pdf")
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"CyberSentinel_Report_{scan_id}.pdf")


# ---------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------

@app.route("/api/scan", methods=["POST"])
def api_start_scan():
    payload = request.get_json(silent=True) or request.form
    target = (payload.get("target") or "").strip()
    scan_type = (payload.get("scan_type") or "quick").strip()
    custom_flags = (payload.get("custom_flags") or "").strip()

    if not target:
        return jsonify({"error": "Target is required."}), 400

    if not nmap_scanner.is_target_allowed(target):
        return jsonify({
            "error": "Target not available in the portfolio demonstration. "
                     "Only approved demonstration hosts can be scanned."
        }), 403

    try:
        nmap_scanner.build_args(scan_type, custom_flags)  # validate early
    except nmap_scanner.InvalidScanOptionsError as e:
        return jsonify({"error": str(e)}), 400

    scan_id = models.create_scan(target, scan_type)
    _set_progress(scan_id, "running")

    thread = threading.Thread(
        target=_run_scan_background,
        args=(scan_id, target, scan_type, custom_flags),
        daemon=True,
    )
    thread.start()

    return jsonify({"scan_id": scan_id}), 202


@app.route("/api/scan/<int:scan_id>/status")
def api_scan_status(scan_id):
    with PROGRESS_LOCK:
        prog = PROGRESS.get(scan_id, {"stage": "queued", "label": "Queued", "percent": 5})
    scan = models.get_scan(scan_id)
    if not scan:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "scan_id": scan_id,
        "db_status": scan["status"],
        "error": scan.get("error"),
        **prog,
    })


@app.route("/api/stats")
def api_stats():
    return jsonify(models.stats())


@app.route("/api/severity-distribution")
def api_severity_distribution():
    return jsonify(models.severity_distribution())


@app.route("/api/allowed-targets")
def api_allowed_targets():
    return jsonify(Config.ALLOWED_TARGETS)


@app.route("/api/discover", methods=["POST"])
def api_discover():
    if not Config.ALLOW_LAN_DISCOVERY:
        return jsonify({"error": "LAN discovery is disabled in config.py."}), 403

    payload = request.get_json(silent=True) or {}
    subnet = (payload.get("subnet") or "").strip() or None

    try:
        used_subnet, devices = discovery.discover_devices(subnet)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        return jsonify({"error": f"Discovery failed: {e}"}), 500

    return jsonify({"subnet": used_subnet, "devices": devices})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
