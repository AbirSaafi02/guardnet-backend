"""
scanner.py — NetworkScanner complet
Détecte les hôtes, ports, services, OS et nouveautés (is_new / is_new_port)
en comparant avec une base de données JSON locale.
"""
import os
os.environ["PATH"] = r"C:\Program Files (x86)\Nmap" + os.pathsep + os.environ.get("PATH", "")
import json
import nmap
import socket
from datetime import datet


# ── Chemin de la base de données locale ───────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "scan_db.json")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_db() -> dict:
    """Charge la base de données JSON (historique des scans précédents)."""
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            return json.load(f)
    return {}


def _save_db(db: dict) -> None:
    """Sauvegarde la base de données JSON."""
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)


def _deduce_device_type(os_name: str) -> str:
    """
    Déduit le type d'appareil à partir du nom de l'OS détecté.

    Exemples :
        "Linux 4.x"           → "server"
        "Windows 10"          → "workstation"
        "iOS 15"              → "mobile"
        "Cisco IOS"           → "router"
        "Synology DiskStation" → "nas"
    """
    if not os_name:
        return "unknown"

    os_lower = os_name.lower()

    rules = [
        (["cisco", "juniper", "mikrotik", "routeros", "extreme networks"], "router"),
        (["switch", "catalyst", "procurve", "netgear gs"],                 "switch"),
        (["android", "ios", "iphone", "ipad", "mobile"],                   "mobile"),
        (["windows 10", "windows 11", "windows 7", "windows 8",
          "macos", "mac os x"],                                             "workstation"),
        (["windows server", "ubuntu server", "centos", "debian",
          "red hat", "fedora", "linux", "freebsd", "unix"],                "server"),
        (["printer", "lexmark", "hp laserjet", "canon"],                   "printer"),
        (["synology", "qnap", "nas"],                                       "nas"),
        (["vmware", "virtualbox", "hyper-v", "xen"],                       "virtual_machine"),
        (["camera", "hikvision", "dahua"],                                  "camera"),
    ]

    for keywords, device_type in rules:
        if any(kw in os_lower for kw in keywords):
            return device_type

    return "unknown"


def _resolve_hostname(ip: str) -> str:
    """Résolution DNS inverse — retourne '' si échec."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# NetworkScanner
# ─────────────────────────────────────────────────────────────────────────────

class NetworkScanner:
    """
    Scanner réseau basé sur python-nmap.

    Usage :
        scanner = NetworkScanner()
        result  = scanner.scan("192.168.1.0/24", scan_type="full")
        print(json.dumps(result, indent=2))
    """

    # Arguments nmap par type de scan
    SCAN_PROFILES = {
        "quick":    "-sV -T4 -Pn -p 22,80,443,8080,8443,3306,5432,21,25,53",
        "full":     "-sV -O -T4 -Pn -p 1-65535",
        "stealth":  "-sS -sV -O -T2 -Pn -p 1-1024",
        "os":       "-O -T4 -Pn",
        "ports":    "-sV -T4 -Pn -p 1-1024",
        "udp":      "-sU -T4 -Pn -p 53,67,68,123,161,162",
    }

    def __init__(self):
        self.scanner = nmap.PortScanner()




    # ── Méthode principale ────────────────────────────────────────────────────

    def scan(self, ip_range: str, scan_type: str = "quick") -> dict:
        """
        Lance un scan nmap sur ip_range.

        Paramètres :
            ip_range  : ex. "192.168.1.1", "192.168.1.0/24", "10.0.0.1-10"
            scan_type : "quick" | "full" | "stealth" | "os" | "ports" | "udp"

        Retourne un dict JSON :
        {
            "scan_info": { "ip_range", "scan_type", "command", "timestamp",
                           "total_hosts", "hosts_up" },
            "hosts": [ { ip, hostname, state, os_name, device_type, is_new,
                         ports: [{port, protocol, service, version, is_new_port}]
                       } ]
        }
        """
        args = self.SCAN_PROFILES.get(scan_type, self.SCAN_PROFILES["quick"])

        print(f"[*] Scan '{scan_type}' sur {ip_range} ...")
        print(f"[*] Arguments nmap : {args}")

        try:
            self.nm.scan(hosts=ip_range, arguments=args)
        except nmap.PortScannerError as e:
            return {"error": str(e)}

        hosts_result = []

        for ip in self.nm.all_hosts():
            host_data = self._parse_host(ip)
            hosts_result.append(host_data)

        # Sauvegarde la base de données mise à jour
        _save_db(self.db)

        result = {
            "scan_info": {
                "ip_range":    ip_range,
                "scan_type":   scan_type,
                "command":     self.nm.command_line(),
                "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_hosts": len(hosts_result),
                "hosts_up":    sum(1 for h in hosts_result if h["state"] == "up"),
            },
            "hosts": hosts_result,
        }

        return result

    # ── Parsing d'un hôte ─────────────────────────────────────────────────────

    def _parse_host(self, ip: str) -> dict:
        """Extrait toutes les infos d'un hôte scanné."""
        host = self.nm[ip]

        # ── État ──────────────────────────────────────────────────────────────
        state = host.state()  # "up" ou "down"

        # ── Hostname ──────────────────────────────────────────────────────────
        hostnames = host.hostnames()
        hostname  = hostnames[0]["name"] if hostnames else _resolve_hostname(ip)

        # ── OS ────────────────────────────────────────────────────────────────
        os_name     = self._extract_os(host)
        device_type = _deduce_device_type(os_name)

        # ── Ports ─────────────────────────────────────────────────────────────
        ports = self._parse_ports(ip, host)

        # ── is_new (comparer avec DB) ─────────────────────────────────────────
        is_new = ip not in self.db

        # ── Mise à jour de la DB ──────────────────────────────────────────────
        self.db[ip] = {
            "hostname":    hostname,
            "os_name":     os_name,
            "device_type": device_type,
            "last_seen":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ports":       [p["port"] for p in ports],
        }

        return {
            "ip":          ip,
            "hostname":    hostname,
            "state":       state,
            "os_name":     os_name,
            "device_type": device_type,
            "is_new":      is_new,
            "ports":       ports,
        }

    # ── Extraction OS ─────────────────────────────────────────────────────────

    def _extract_os(self, host) -> str:
        """Retourne le nom de l'OS le plus probable ou ''."""
        try:
            osmatch = host["osmatch"]
            if osmatch:
                return osmatch[0]["name"]
        except (KeyError, IndexError):
            pass
        return ""

    # ── Parsing des ports ─────────────────────────────────────────────────────

    def _parse_ports(self, ip: str, host) -> list:
        """Retourne la liste des ports avec leurs détails."""
        ports_result = []
        known_ports  = set(self.db.get(ip, {}).get("ports", []))

        for proto in host.all_protocols():
            for port, info in sorted(host[proto].items()):

                service = info.get("name", "")
                version = " ".join(filter(None, [
                    info.get("product", ""),
                    info.get("version", ""),
                    info.get("extrainfo", ""),
                ])).strip()

                is_new_port = port not in known_ports

                ports_result.append({
                    "port":        port,
                    "protocol":    proto,
                    "service":     service,
                    "version":     version if version else "unknown",
                    "state":       info.get("state", "unknown"),
                    "is_new_port": is_new_port,
                })

        return ports_result


# ─────────────────────────────────────────────────────────────────────────────
# Test rapide (lancer directement : python scanner.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    scanner = NetworkScanner()

    # Scan localhost en mode rapide
    result = scanner.scan("127.0.0.1", scan_type="quick")

    print("\n" + "=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60)

    # Résumé
    info  = result["scan_info"]
    hosts = result["hosts"]

    print(f"\n✅ Scan terminé : {info['total_hosts']} hôte(s) trouvé(s), "
          f"{info['hosts_up']} en ligne")

    for h in hosts:
        new_tag = " 🆕 NOUVEAU" if h["is_new"] else ""
        print(f"\n  📍 {h['ip']} ({h['hostname'] or 'no-hostname'}){new_tag}")
        print(f"     OS     : {h['os_name'] or 'inconnu'}")
        print(f"     Type   : {h['device_type']}")
        print(f"     État   : {h['state']}")
        print(f"     Ports  : {len(h['ports'])} trouvé(s)")
        for p in h["ports"]:
            new_port = " 🆕" if p["is_new_port"] else ""
            print(f"       {p['port']}/{p['protocol']:3}  [{p['state']:6}]  "
                  f"{p['service']:12}  {p['version']}{new_port}")