"""
VPN & GoldSrc Server Ping / Status Check Tool (MP01, MP15).
Detects Tailscale, ZeroTier, Radmin/Hamachi, and LAN IPv4 addresses,
checks ICMP reachability, and queries live Condition Zero servers via UDP A2S_INFO.
"""

import argparse
import ipaddress
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from multiplayer import DEFAULT_SERVER_PORT, MOD_VERSION


def _is_tailscale_cgnat(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj in ipaddress.ip_network("100.64.0.0/10")
    except ValueError:
        return False


def _run_cmd_quiet(args: list[str], timeout: float = 2.0) -> str:
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore",
        )
        if proc.returncode == 0:
            return (proc.stdout or "").strip()
    except Exception:
        pass
    return ""


def _detect_tailscale_cli() -> str | None:
    candidates = []
    which_ts = shutil.which("tailscale")
    if which_ts:
        candidates.append(which_ts)
    if os.name == "nt":
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        candidates.append(os.path.join(pf, "Tailscale", "tailscale.exe"))

    for exe in candidates:
        if os.path.exists(exe):
            out = _run_cmd_quiet([exe, "ip", "-4"], timeout=2.0)
            for line in out.splitlines():
                candidate = line.strip()
                if _is_tailscale_cgnat(candidate):
                    return candidate
    return None


def parse_ipconfig_adapters(ipconfig_text: str) -> list[dict]:
    """
    Parse Windows `ipconfig /all` text into a list of adapter dicts:
    [{"name": str, "description": str, "ipv4": list[str]}]
    """
    adapters = []
    current = None

    for raw_line in ipconfig_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue

        # Adapter header lines do not start with whitespace and end with ':'
        if not raw_line[0].isspace() and line.endswith(":"):
            if current and current["ipv4"]:
                adapters.append(current)
            current = {
                "name": line[:-1].strip(),
                "description": "",
                "ipv4": [],
            }
            continue

        if current is None:
            continue

        low = line.lower()
        if "description" in low and ":" in line:
            current["description"] = line.split(":", 1)[1].strip()
        elif ("ipv4" in low or "ip address" in low) and ":" in line:
            val = line.split(":", 1)[1].strip()
            # Strip '(Preferred)' suffix
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", val)
            if m:
                ip_val = m.group(1)
                if not ip_val.startswith("127.") and not ip_val.startswith("169.254."):
                    current["ipv4"].append(ip_val)

    if current and current["ipv4"]:
        adapters.append(current)

    return adapters


def detect_network_addresses(ipconfig_override: str | None = None) -> dict:
    """
    Detect VPN IPs (Tailscale, ZeroTier, Radmin, Hamachi) and LAN IPv4 address.
    Returns:
      {
        "vpn_provider": str | None,
        "vpn_ip": str | None,
        "lan_ip": str | None,
        "all_vpn": [{"provider": str, "ip": str, "adapter": str}],
        "preferred_ip": str,
      }
    """
    all_vpn = []
    lan_ip = None

    # 1. Check Tailscale CLI first if not testing an override
    if ipconfig_override is None:
        ts_ip = _detect_tailscale_cli()
        if ts_ip:
            all_vpn.append({"provider": "Tailscale", "ip": ts_ip, "adapter": "Tailscale CLI"})

    # 2. Parse ipconfig /all
    raw_ipconfig = ipconfig_override if ipconfig_override is not None else _run_cmd_quiet(["ipconfig", "/all"], timeout=3.0)
    for ad in parse_ipconfig_adapters(raw_ipconfig):
        meta = f"{ad['name']} {ad['description']}".lower()
        for ip_val in ad["ipv4"]:
            provider = None
            if "tailscale" in meta or _is_tailscale_cgnat(ip_val):
                provider = "Tailscale"
            elif "zerotier" in meta:
                provider = "ZeroTier"
            elif "radmin" in meta or ip_val.startswith("26."):
                provider = "Radmin VPN"
            elif "hamachi" in meta or ip_val.startswith("25."):
                provider = "Hamachi"
            elif "wireguard" in meta or "tun" in meta or "tap" in meta:
                provider = "VPN Tunnel"

            if provider:
                if not any(v["ip"] == ip_val for v in all_vpn):
                    all_vpn.append({"provider": provider, "ip": ip_val, "adapter": ad["name"]})
            else:
                if lan_ip is None:
                    lan_ip = ip_val

    # 3. Fallback LAN IP detection via UDP socket routing table lookup
    if lan_ip is None and ipconfig_override is None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                cand = s.getsockname()[0]
                if cand and not cand.startswith("127.") and not _is_tailscale_cgnat(cand):
                    lan_ip = cand
        except Exception:
            pass

    vpn_provider = all_vpn[0]["provider"] if all_vpn else None
    vpn_ip = all_vpn[0]["ip"] if all_vpn else None
    preferred_ip = vpn_ip or lan_ip or "127.0.0.1"

    return {
        "vpn_provider": vpn_provider,
        "vpn_ip": vpn_ip,
        "lan_ip": lan_ip,
        "all_vpn": all_vpn,
        "preferred_ip": preferred_ip,
    }


def _read_cstring(buf: bytes, offset: int) -> tuple[str, int]:
    end = buf.find(b"\x00", offset)
    if end == -1:
        return buf[offset:].decode("utf-8", errors="replace"), len(buf)
    return buf[offset:end].decode("utf-8", errors="replace"), end + 1


def parse_a2s_info_response(data: bytes) -> dict | None:
    """
    Parse GoldSrc / Source A2S_INFO response packet (both 0x49 'I' and legacy 0x6D 'm').
    Returns dict with name, map, folder, game, players, max_players, bots, or None if invalid.
    """
    if not data or len(data) < 6 or not data.startswith(b"\xFF\xFF\xFF\xFF"):
        return None

    header = data[4]
    idx = 5

    # Modern A2S_INFO ('I' = 0x49)
    if header == 0x49:
        if idx >= len(data):
            return None
        protocol = data[idx]
        idx += 1
        name, idx = _read_cstring(data, idx)
        map_name, idx = _read_cstring(data, idx)
        folder, idx = _read_cstring(data, idx)
        game, idx = _read_cstring(data, idx)
        if idx + 5 > len(data):
            return None
        # Skip 2-byte steam appid
        idx += 2
        players = data[idx]
        max_players = data[idx + 1]
        bots = data[idx + 2]
        return {
            "format": "source_I",
            "protocol": protocol,
            "name": name,
            "map": map_name,
            "folder": folder,
            "game": game,
            "players": players,
            "max_players": max_players,
            "bots": bots,
        }

    # Legacy GoldSrc A2S_INFO ('m' = 0x6D)
    if header == 0x6D:
        _address, idx = _read_cstring(data, idx)
        name, idx = _read_cstring(data, idx)
        map_name, idx = _read_cstring(data, idx)
        folder, idx = _read_cstring(data, idx)
        game, idx = _read_cstring(data, idx)
        if idx + 2 > len(data):
            return None
        players = data[idx]
        max_players = data[idx + 1]
        protocol = data[idx + 2] if idx + 2 < len(data) else 47
        return {
            "format": "goldsrc_m",
            "protocol": protocol,
            "name": name,
            "map": map_name,
            "folder": folder,
            "game": game,
            "players": players,
            "max_players": max_players,
            "bots": 0,
        }

    return None


def query_goldsrc_server(host: str, port: int = DEFAULT_SERVER_PORT, timeout: float = 2.0) -> dict:
    """
    Send UDP A2S_INFO query to a Condition Zero server (handles challenge 0x41 automatically).
    Returns:
      {
        "online": bool,
        "ping_ms": float | None,
        "info": dict | None,
        "error": str | None,
      }
    """
    request = b"\xFF\xFF\xFF\xFFTSource Engine Query\x00"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            t0 = time.perf_counter()
            sock.sendto(request, (host, port))
            data, _ = sock.recvfrom(4096)
            rtt_ms = round((time.perf_counter() - t0) * 1000.0, 1)

            # Handle A2S_INFO challenge ('A' = 0x41)
            if len(data) >= 9 and data.startswith(b"\xFF\xFF\xFF\xFF\x41"):
                challenge = data[5:9]
                t1 = time.perf_counter()
                sock.sendto(request + challenge, (host, port))
                data, _ = sock.recvfrom(4096)
                rtt_ms = round((time.perf_counter() - t1) * 1000.0, 1)

            parsed = parse_a2s_info_response(data)
            if parsed:
                return {"online": True, "ping_ms": rtt_ms, "info": parsed, "error": None}
            return {"online": False, "ping_ms": rtt_ms, "info": None, "error": "Unrecognized server response"}
    except socket.timeout:
        return {"online": False, "ping_ms": None, "info": None, "error": f"Timed out waiting for UDP {host}:{port}"}
    except Exception as e:
        return {"online": False, "ping_ms": None, "info": None, "error": str(e)}


def ping_host_icmp(host: str, timeout_ms: int = 1500) -> float | None:
    """Run single ICMP ping to verify VPN reachability even when game server isn't open yet."""
    if os.name == "nt":
        out = _run_cmd_quiet(["ping", "-n", "1", "-w", str(timeout_ms), host], timeout=(timeout_ms / 1000.0) + 1.5)
    else:
        out = _run_cmd_quiet(["ping", "-c", "1", "-W", "2", host], timeout=3.0)

    if not out:
        return None
    m = re.search(r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms", out, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None


def parse_host_port(target: str, default_port: int = DEFAULT_SERVER_PORT) -> tuple[str, int]:
    cleaned = target.strip()
    if cleaned.lower().startswith("connect "):
        cleaned = cleaned[8:].strip()
    if ":" in cleaned:
        h, p_str = cleaned.rsplit(":", 1)
        try:
            return h.strip(), int(p_str.strip())
        except ValueError:
            return h.strip(), default_port
    return cleaned, default_port


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CZ AI Teammates — VPN & Server Ping Check Tool (MP15)")
    parser.add_argument("target", nargs="?", default="", help="Optional Host VPN IP (e.g., 100.84.12.5 or 100.84.12.5:27015)")
    args = parser.parse_args(argv)

    print("=================================================================")
    print(f"  CZ AI TEAMMATES MULTIPLAYER — VPN & PING CHECK ({MOD_VERSION})")
    print("=================================================================")

    net = detect_network_addresses()
    if net["all_vpn"]:
        print("  [OK] VPN Tunnel Detected:")
        for v in net["all_vpn"]:
            print(f"       - {v['provider']}: {v['ip']} ({v['adapter']})")
    else:
        print("  [!] No active VPN tunnel (Tailscale / ZeroTier) detected.")
        print("      Install Tailscale (https://tailscale.com/download) or ZeroTier")
        print("      so friends over the internet can connect with zero port forwarding.")

    if net["lan_ip"]:
        print(f"  [i] Local LAN IPv4 : {net['lan_ip']}")
    print(f"  [i] Shareable Host : connect {net['preferred_ip']}:{DEFAULT_SERVER_PORT}")
    print("-----------------------------------------------------------------")

    target = args.target.strip()
    if target:
        host, port = parse_host_port(target)
        print(f"  Testing connection to {host}:{port} ...")
        icmp_ms = ping_host_icmp(host)
        if icmp_ms is not None:
            quality = "EXCELLENT" if icmp_ms < 50 else ("GOOD" if icmp_ms < 110 else "HIGH PING")
            print(f"  [OK] VPN ICMP Ping : {icmp_ms:.0f} ms ({quality})")
        else:
            print("  [!] ICMP Ping     : No reply (firewall may block ICMP, testing UDP 27015...)")

        res = query_goldsrc_server(host, port=port, timeout=2.5)
        if res["online"] and res["info"]:
            info = res["info"]
            print(f"  [OK] CZ Server    : ONLINE ({res['ping_ms']} ms UDP RTT)")
            print(f"       Match Name   : {info['name']}")
            print(f"       Map          : {info['map']}")
            print(f"       Players      : {info['players']} / {info['max_players']} (Bots: {info['bots']})")
            print(f"       Join Command : connect {host}:{port}")
        else:
            print(f"  [!] CZ Server     : Not responding on UDP {host}:{port} ({res['error']})")
            print("      Make sure the host ran host.bat and started the map, and allow hl.exe/hlds.exe in Windows Firewall.")
        print("=================================================================")

    return 0


if __name__ == "__main__":
    sys.exit(main())

