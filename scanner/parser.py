"""
CyberSentinel - Parser
-------------------------------
Turns a python-nmap PortScanner result into the plain-dict structures
the rest of the app (DB layer, reports, dashboard) works with.
"""


def parse_scan(scanner, target: str):
    """
    scanner: an nmap.PortScanner instance *after* .scan() has been called.
    Returns: {
        "hostname": str,
        "state": str,
        "os_guess": str | None,
        "services": [ {port, protocol, service, version, state}, ... ]
    }
    """
    hosts = scanner.all_hosts()
    if not hosts:
        return {
            "hostname": target,
            "state": "down",
            "os_guess": None,
            "services": [],
        }

    host = hosts[0]
    host_info = scanner[host]

    hostname = host_info.hostname() or target
    state = host_info.state()

    os_guess = None
    if "osmatch" in host_info and host_info["osmatch"]:
        best = host_info["osmatch"][0]
        os_guess = f"{best.get('name')} ({best.get('accuracy')}% confidence)"

    services = []
    for proto in host_info.all_protocols():
        ports = sorted(host_info[proto].keys())
        for port in ports:
            entry = host_info[proto][port]
            version_parts = [
                entry.get("product", ""),
                entry.get("version", ""),
            ]
            version = " ".join(p for p in version_parts if p).strip()
            services.append(
                {
                    "port": port,
                    "protocol": proto,
                    "service": entry.get("name", "unknown"),
                    "version": version or "unknown",
                    "state": entry.get("state", "unknown"),
                }
            )

    return {
        "hostname": hostname,
        "state": state,
        "os_guess": os_guess,
        "services": services,
    }
