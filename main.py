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
                "channel": "?",
                "band": "?"
            }
            networks.append(current)
        elif current is not None and line.startswith("Authentication"):
            current["auth"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("Signal") and current["signal"] == "?":
            current["signal"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("Channel") and current["channel"] == "?":
            current["channel"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("Band") and current["band"] == "?":
            current["band"] = line.split(":", 1)[1].strip()
    return networks

def mark_mixed_names(networks):
    for i in range(len(networks)):
        for j in range(len(networks)):
            if i == j:
                continue
            if networks[i]["name"] == "(hidden)":
                continue
            same_name = networks[i]["name"] == networks[j]["name"]
            different_auth = networks[i]["auth"] != networks[j]["auth"]
            if same_name and different_auth:
                networks[i]["mixed"] = True

def count_on_channel(networks, channel):
    if channel == "?":
        return 0
    count = 0
    for item in networks:
        if item["channel"] == channel:
            count = count+1
    return count

def rate_network(item,crowd):
    reasons = []
    score, label = security_score(item["auth"])
    reasons.append(label + " security")
    signal_text = item["signal"].replace("%","").strip()
    signal_number = -1
    if signal_text.isdigit():
        signal_number = int(signal_text)
    if signal_number >= 0 and signal_number <40:
        score = score-2
        reasons.append("weak signal")
    elif signal_number >= 70:
        reasons.append("strong signal")
    elif signal_number >= 0:
        score = score-1
        reasons.append("medium signal")
    band = item["band"].lower()
    if "2.4" in band:
        score = score-1
        reasons.append("2.4 GHz is more crowded")
    elif "5" in band:
        reasons.append("5 GHz band")
    others = crowd-1
    if others <0:
        others = 0
    elif others >=3:
        score = score-2
        reasons.append("channel is crowded")
    elif others >=1:
        score = score-1
        reasons.append("others networks on this channel")
    if item.get("mixed") == True:
        score = score-3
        reasons.append("same name has different security")
    if score <0:
        score=0
    if score >10:
        score=10
    return score,reasons
def show_networks(networks):
    mark_mixed_names(networks)
    print("Found", len(networks), "network(s)")
    print("")
    for item in networks:
        crowd = count_on_channel(networks, item["channel"])
        score, reasons = rate_network(item, crowd)
        print(item["name"])
        print(" score:",str(score)+ "/10")
        print(" security:", item["auth"])
        print( "signal:", item["signal"])
        print(" channel:", item["channel"])
        print(" band:", item["band"])
        print(" why:")
        for reason in reasons:
            print(" -", reason)
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