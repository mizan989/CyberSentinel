# CyberSentinel

Automated Vulnerability Scanner & Reporting Dashboard — a portfolio project
demonstrating full-stack Python + basic security-automation skills.

> **This tool does not exploit anything.** It performs read-only host/service
> discovery (via Nmap), matches services against a small offline CVE lookup
> table, scores risk, and generates HTML/PDF reports — restricted to an
> explicit allowlist of authorized demo targets.

## Features

- Host discovery, port scanning, service + OS detection (via `python-nmap`)
- Offline CVE lookup / matching (no external API calls at scan time)
- 0–100 risk scoring with severity breakdown
- Scan history with search
- HTML report view + downloadable PDF report (ReportLab)
- Live-updating scan progress
- Dark, cybersecurity-themed dashboard (Bootstrap 5 + Chart.js)
- Dockerized deployment behind Nginx

## Important: safety boundary

Scans are hard-restricted to the allowlist in `config.py`:

```python
ALLOWED_TARGETS = [
    "scanme.nmap.org",   # Nmap's own official public test target
    "127.0.0.1",
    "localhost",
]
```

`scanme.nmap.org` is provided by the Nmap project specifically for people to
practice scanning against. If you want to scan anything else — including
your own servers — add it to `ALLOWED_TARGETS` only once you have the
authority to test it. **Scanning systems you don't own or don't have
explicit written permission to test is illegal in most jurisdictions.**

## Local setup

Requires the `nmap` binary installed on your system (not just the Python
package) — e.g. `sudo apt install nmap` on Debian/Ubuntu, `brew install nmap`
on macOS.

```bash
python3 -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install -r requirements.txt

python app.py                     # dev server on http://localhost:5000
```

The SQLite database (`database.db`) and folders `scans/` and
`reports_output/` are created automatically on first run.

## Production

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

## Docker

```bash
cd Docker
docker compose up --build
```

This brings up:
- `web` — the Flask app (with `nmap` installed in the image) served by Gunicorn
- `nginx` — reverse proxy on port 80

To add HTTPS, mount a certificate into `Docker/certs` and uncomment the
`443`/`ssl_certificate` lines in `nginx.conf` and `docker-compose.yml`.

## Project structure

```
CyberSentinel/
├── app.py                 # Flask app + routes + background scan runner
├── config.py               # Allowlist, scan profiles, paths
├── requirements.txt
├── scanner/
│   ├── nmap_scanner.py     # Runs nmap, enforces allowlist
│   ├── parser.py           # Turns python-nmap results into plain dicts
│   ├── vulnerability.py    # Offline CVE lookup table + matcher
│   └── risk.py              # Risk scoring
├── reports/
│   ├── html.py              # Renders report.html for standalone use
│   └── pdf.py                # Builds the PDF report (ReportLab)
├── database/
│   └── models.py            # sqlite3 schema + helper functions
├── static/{css,js,images}
├── templates/               # Jinja2 templates (dark theme)
├── scans/                   # Raw scan artifacts
├── reports_output/          # Generated PDF reports
└── Docker/                  # Dockerfile, docker-compose.yml, nginx.conf
```

## Extending the CVE data

`scanner/vulnerability.py` contains `CVE_DATABASE`, a small hand-written
dictionary of service → known CVE rules with simple substring version
matching. It's intentionally offline/static for a demo. To make this more
rigorous, you'd swap in proper CPE-based matching against the NVD API — just
be mindful that adds an external network dependency at scan/report time.

## License

MIT — see `LICENSE`.
