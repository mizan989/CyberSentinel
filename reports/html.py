"""
CyberSentinel - HTML Report
-------------------------------
The HTML report re-uses the Flask/Jinja2 templates/report.html template
(same one shown in-app), so there's a single source of truth for the
report layout. This module just renders it to a standalone string so
it can be saved to disk or served as a download.
"""

from flask import render_template


def render_html_report(scan_data):
    return render_template("report.html", scan=scan_data, standalone=True)
