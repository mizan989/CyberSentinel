"""
CyberSentinel - Configuration
-------------------------------
Central place for app settings, allowlisted scan targets, and scan-type
definitions. Keeping the allowlist here (instead of buried in a route)
makes the "safety boundary" of the whole app easy to audit at a glance.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("CYBERSENTINEL_SECRET_KEY", "dev-secret-change-me")

    # SQLite database file
    DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

    # Where raw nmap XML output and generated reports are written
    SCANS_DIR = os.path.join(BASE_DIR, "scans")
    REPORTS_DIR = os.path.join(BASE_DIR, "reports_output")

    # -----------------------------------------------------------------
    # SAFETY BOUNDARY
    # Only these hosts may ever be scanned by this application. This is
    # a portfolio / demo project, so it must never be usable to scan
    # arbitrary third-party infrastructure without explicit permission.
    # scanme.nmap.org is Nmap's own official, publicly authorized test
    # target, intended by its maintainers to be scanned for exactly
    # this kind of learning/demo purpose.
    # -----------------------------------------------------------------
    ALLOWED_TARGETS = [
        "scanme.nmap.org",
        "127.0.0.1",
        "localhost",
        # Add your own authorized demo VPS/hostname below once you have
        # written permission to scan it, e.g.:
        # "your-demo-vps.com",
    ]

    # -----------------------------------------------------------------
    # LAN DISCOVERY MODE
    # When True, any private/local-network IP address (RFC1918 ranges,
    # loopback, link-local) is automatically allowed as a scan target,
    # in addition to ALLOWED_TARGETS above. This is what powers the
    # "Discover Network" feature: it lets you scan devices you find on
    # your own LAN without hand-adding every IP to the allowlist.
    #
    # This does NOT open scanning up to the public internet — an IP
    # outside the private ranges is still rejected. Turn this off if
    # you only ever want the fixed ALLOWED_TARGETS list to be scannable.
    # -----------------------------------------------------------------
    ALLOW_LAN_DISCOVERY = True

    # Scan type -> nmap argument string
    SCAN_PROFILES = {
        "quick": {
            "label": "Quick (Top 100 Ports)",
            "args": "-F -T4",
        },
        "normal": {
            "label": "Normal (Top 1000 Ports)",
            "args": "-T4",
        },
        "intense": {
            "label": "Intense (Version + OS + Scripts)",
            "args": "-T4 -A -sV -O",
        },
        "custom": {
            "label": "Custom",
            "args": None,  # supplied by the user, still validated
        },
    }

    # Whitelisted extra flags a user may add when "custom" is selected.
    # Prevents arbitrary flag injection (e.g. -oN /etc/passwd style abuse).
    CUSTOM_ALLOWED_FLAGS = {
        "-F", "-T0", "-T1", "-T2", "-T3", "-T4", "-T5",
        "-sV", "-O", "-A", "-Pn", "-p-", "--top-ports",
    }

    RISK_LEVELS = ["Informational", "Low", "Medium", "High", "Critical"]
