"""
CyberSentinel - Scan Engine
-------------------------------
Thin wrapper around python-nmap. Responsible only for *running* nmap and
handing back the raw XML / PortScanner result. All interpretation of the
result happens in parser.py.

Every call is gated by the allowlist in config.py — this module refuses
to scan anything not explicitly approved, no matter what called it.
"""

import ipaddress
import shlex

import nmap

from config import Config


class TargetNotAllowedError(Exception):
    pass


class InvalidScanOptionsError(Exception):
    pass


def is_target_allowed(target: str) -> bool:
    target = target.strip().lower()

    if target in {t.lower() for t in Config.ALLOWED_TARGETS}:
        return True

    if Config.ALLOW_LAN_DISCOVERY:
        try:
            ip = ipaddress.ip_address(target)
        except ValueError:
            return False
        # Private (RFC1918), loopback, and link-local ranges only.
        # This is the safety boundary for LAN discovery mode: it can
        # never match a public internet address.
        return ip.is_private or ip.is_loopback or ip.is_link_local

    return False


def build_args(scan_type: str, custom_flags: str = "") -> str:
    profile = Config.SCAN_PROFILES.get(scan_type)
    if profile is None:
        raise InvalidScanOptionsError(f"Unknown scan type: {scan_type}")

    if scan_type != "custom":
        return profile["args"]

    # Custom scans: only allow flags from an explicit safe list to stop
    # flag-injection (e.g. -oN, --script=, shell metacharacters, etc.)
    tokens = shlex.split(custom_flags or "")
    for tok in tokens:
        base = tok.split("=")[0]
        if base not in Config.CUSTOM_ALLOWED_FLAGS:
            raise InvalidScanOptionsError(f"Flag not permitted in demo mode: {tok}")
    return " ".join(tokens) if tokens else "-F -T4"


def run_scan(target: str, scan_type: str, custom_flags: str = ""):
    """
    Runs an nmap scan and returns the python-nmap PortScanner object plus
    the raw XML string (useful for the "Generate XML" / "Parse XML"
    steps described in the blueprint).
    """
    if not is_target_allowed(target):
        raise TargetNotAllowedError(
            "Target not available in the portfolio demonstration. "
            "Only approved demonstration hosts can be scanned."
        )

    args = build_args(scan_type, custom_flags)

    scanner = nmap.PortScanner()
    scanner.scan(hosts=target, arguments=args)
    raw_xml = scanner.get_nmap_last_output()
    return scanner, raw_xml
