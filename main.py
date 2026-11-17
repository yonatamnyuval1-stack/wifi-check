import subprocess

def get_wifi_text():
    result = subprocess.run(
        ["netsh","wlan","show","networks","mode=bssid"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if result.returncode != 0:
        print("Scan failed")
        if result.stderr:
            print(result.stderr.strip())
        return ""
    return result.stdout

def security_score(auth):
    text = auth.lower()
    if "wpa3" in text:
        return 9, "strong"
    if "wpa2" in text:
        return 7, "ok"
    if "wpa" in text:
        return 4, "weak"
    if "wep" in text:
        return 2, "bad"
    if "open" in text:
        return 1, "bad"
    return 0, "unknown"

def read_networks(text):
    networks = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("SSID ") and ":" in line:
            name = line.split(":", 1)[1].strip()
            if name == "":
                name = "(hidden)"
            current = {
                "name": name,
                "auth": "unknown",
                "signal": "?",
            }
            networks.append(current)
        elif current is not None and line.startswith("Authentication"):
            current["auth"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("Signal") and current["signal"] == "?":
            current["signal"] = line.split(":", 1)[1].strip()
    return networks

def show_networks(networks):
    print("Found", len(networks), "network(s)")
    print("")
    for item in networks:
        score, label = security_score(item["auth"])
        print(item["name"])
        print(" security:", item["auth"])
        print(" signal:", item["signal"])
        print(" score:", str(score) + "/10", "(" + label + ")")
        print("")
text = get_wifi_text()
if text.strip() == "":
    print("No scan output")
else:
    networks = read_networks(text)
    if len(networks) == 0:
        print("No networks found")
    else:
        show_networks(networks)