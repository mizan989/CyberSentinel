"""
CyberSentinel - Network Discovery
-------------------------------
Finds live devices on the local LAN so the user can pick one to run a
full vulnerability scan against, instead of having to already know an
IP address.

Uses `nmap -sn` (a "ping scan" — host discovery only, no port scan),
which is fast and lightweight compared to a full scan.

Safety note: discovery itself is always restricted to private/LAN
address ranges (see auto-detected subnet below), so this can never be
pointed at the public internet.
"""

import ipaddress
import socket

import nmap


def get_local_ip_and_subnet():
    """
    Best-effort detection of this machine's LAN IP and a /24 subnet to
    scan. Uses a UDP "connect" (no packets actually sent) as a portable
    way to find which local interface would be used to reach the
    internet, then assumes a standard /24 home-network mask.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except OSError:
        local_ip = "127.0.0.1"

    try:
        network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
        subnet = str(network)
    except ValueError:
        subnet = "192.168.1.0/24"

    return local_ip, subnet


def discover_devices(subnet: str = None):
    """
    Runs an nmap ping-scan across `subnet` (defaults to the local /24)
    and returns (subnet_used, [devices]).

    Each device: {ip, hostname, mac, vendor, state}

    Note: MAC address / vendor detection typically requires the nmap
    process to have raw-socket privileges (e.g. running as root/sudo,
    or with the appropriate capabilities on Linux). Without that, mac
    and vendor will show as "unknown" — IP/hostname/state still work.
    """
    local_ip, default_subnet = get_local_ip_and_subnet()
    target_subnet = subnet or default_subnet

    # Guard rail: only ever scan private ranges here, regardless of
    # what was passed in, so discovery can't be pointed at the public
    # internet even if a caller passes a bad value.
    network = ipaddress.ip_network(target_subnet, strict=False)
    if not (network.is_private or network.is_loopback or network.is_link_local):
        raise ValueError("Discovery is restricted to private/LAN network ranges.")

    scanner = nmap.PortScanner()
    scanner.scan(hosts=target_subnet, arguments="-sn -T4")

    devices = []
    for host in scanner.all_hosts():
        info = scanner[host]
        addresses = info.get("addresses", {})
        mac = addresses.get("mac")
        vendor_map = info.get("vendor", {})
        vendor = vendor_map.get(mac) if mac else None

        devices.append(
            {
                "ip": host,
                "hostname": info.hostname() or "",
                "mac": mac or "unknown",
                "vendor": vendor or "unknown",
                "state": info.state(),
                "is_this_device": host == local_ip,
            }
        )

    devices.sort(key=lambda d: tuple(int(p) for p in d["ip"].split(".")))
    return target_subnet, devices
