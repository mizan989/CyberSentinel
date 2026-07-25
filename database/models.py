"""
CyberSentinel - Database layer
-------------------------------
Plain sqlite3 (no ORM) to match the blueprint's tech stack. Small helper
functions wrap all reads/writes so the rest of the app never has to
write raw SQL.
"""

import sqlite3
import json
import threading
from contextlib import contextmanager
from datetime import datetime

from config import Config

_lock = threading.Lock()


def _connect():
    conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_conn():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                duration_seconds REAL,
                status TEXT NOT NULL DEFAULT 'queued',
                risk_score REAL,
                risk_level TEXT,
                os_guess TEXT,
                error TEXT
            );

            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                port INTEGER,
                protocol TEXT,
                service TEXT,
                version TEXT,
                state TEXT
            );

            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                service TEXT,
                version TEXT,
                severity TEXT,
                cve TEXT,
                description TEXT,
                recommendation TEXT
            );
            """
        )


# ---------------------------------------------------------------------
# Scans
# ---------------------------------------------------------------------

def create_scan(target, scan_type):
    with _lock, get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO scans (target, scan_type, started_at, status) "
            "VALUES (?, ?, ?, ?)",
            (target, scan_type, datetime.utcnow().isoformat(), "queued"),
        )
        return cur.lastrowid


def update_scan_status(scan_id, status, error=None):
    with _lock, get_conn() as conn:
        conn.execute(
            "UPDATE scans SET status = ?, error = ? WHERE id = ?",
            (status, error, scan_id),
        )


def finish_scan(scan_id, duration_seconds, risk_score, risk_level, os_guess):
    with _lock, get_conn() as conn:
        conn.execute(
            """UPDATE scans
               SET status = 'finished', finished_at = ?, duration_seconds = ?,
                   risk_score = ?, risk_level = ?, os_guess = ?
               WHERE id = ?""",
            (
                datetime.utcnow().isoformat(),
                duration_seconds,
                risk_score,
                risk_level,
                os_guess,
                scan_id,
            ),
        )


def get_scan(scan_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
        return dict(row) if row else None


def list_scans(limit=50, search=None):
    with get_conn() as conn:
        if search:
            rows = conn.execute(
                "SELECT * FROM scans WHERE target LIKE ? "
                "ORDER BY id DESC LIMIT ?",
                (f"%{search}%", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


def stats():
    with get_conn() as conn:
        total_scans = conn.execute("SELECT COUNT(*) c FROM scans").fetchone()["c"]
        hosts = conn.execute("SELECT COUNT(DISTINCT target) c FROM scans").fetchone()["c"]
        open_ports = conn.execute(
            "SELECT COUNT(*) c FROM services WHERE state = 'open'"
        ).fetchone()["c"]
        vulns = conn.execute("SELECT COUNT(*) c FROM vulnerabilities").fetchone()["c"]
        return {
            "total_scans": total_scans,
            "hosts": hosts,
            "open_ports": open_ports,
            "vulnerabilities": vulns,
        }


def severity_distribution():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT severity, COUNT(*) c FROM vulnerabilities GROUP BY severity"
        ).fetchall()
        return {r["severity"]: r["c"] for r in rows}


# ---------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------

def add_services(scan_id, services):
    with _lock, get_conn() as conn:
        conn.executemany(
            "INSERT INTO services (scan_id, port, protocol, service, version, state) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    scan_id,
                    s.get("port"),
                    s.get("protocol"),
                    s.get("service"),
                    s.get("version"),
                    s.get("state"),
                )
                for s in services
            ],
        )


def get_services(scan_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM services WHERE scan_id = ? ORDER BY port", (scan_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# Vulnerabilities
# ---------------------------------------------------------------------

def add_vulnerabilities(scan_id, vulns):
    with _lock, get_conn() as conn:
        conn.executemany(
            """INSERT INTO vulnerabilities
               (scan_id, service, version, severity, cve, description, recommendation)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    scan_id,
                    v.get("service"),
                    v.get("version"),
                    v.get("severity"),
                    v.get("cve"),
                    v.get("description"),
                    v.get("recommendation"),
                )
                for v in vulns
            ],
        )


def get_vulnerabilities(scan_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM vulnerabilities WHERE scan_id = ? "
            "ORDER BY CASE severity "
            "WHEN 'Critical' THEN 0 WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 "
            "WHEN 'Low' THEN 3 ELSE 4 END",
            (scan_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def full_report_data(scan_id):
    scan = get_scan(scan_id)
    if not scan:
        return None
    scan["services"] = get_services(scan_id)
    scan["vulnerabilities"] = get_vulnerabilities(scan_id)
    return scan
