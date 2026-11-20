# MIT License
# Copyright (c) 2026 Jonathan Jacob

import subprocess
import time

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
        elif current is not None and line.startswith("Signal"):
            new_signal = line.split(":", 1)[1].strip()
            new_text = new_signal.replace("%","").strip()
            old_text = current["signal"].replace("%","").strip()
            new_number = -1
            old_number = -1
            if new_text.isdigit():
                new_number = int(new_text)
            if old_text.isdigit():
                old_number = int(old_text)
            if current["signal"] == "?" or new_number > old_number:
                current["signal"] = new_signal
                current["channel"] = "?"
                current["band"] = "?"
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

def channel_rows(networks):
    rows = []
    for item in networks:
        channel = item["channel"]
        if channel == "?":
            continue
        found = False
        for row in rows:
            if row["channel"] == channel:
                row["count"] = row["count"]+1
                found = True
        if found == False:
            new_row = {
                "channel": channel,
                "band": item["band"],
                "count": 1
            }
            rows.append(new_row)
    for i in range(len(rows)):
        for j in range(len(rows)-1):
            left = rows[j]["channel"]
            right = rows[j+1]["channel"]
            left_num = -1
            right_num = -1
            if left.isdigit():
                left_num = int(left)
            if right.isdigit():
                right_num = int(right)
            if left_num>right_num:
                temp = rows[j]
                rows[j] = rows[j+1]
                rows[j+1] = temp
    return rows
def show_channels(networks):
    rows = channel_rows(networks)
    print("")
    print("channels")
    if len(rows) == 0:
        print("no channels")
        return
    quiet = rows[0]
    for row in rows:
        if row["count"] < quiet["count"]:
            quiet=row
        marks = ""
        n= 0
        while n < row["count"]:
            marks = marks + "#"
            n=n+1
        channel_text = row["channel"]
        while len(channel_text) < 4:
            channel_text = channel_text + " "
        band_text = row["band"]
        while len(band_text) < 10:
            band_text = band_text+" "
        while len(marks) <6:
            marks = marks+" "
        print(" " + channel_text+band_text+marks+str(row["count"]))
    print(" quietest:",quiet["channel"],"on",quiet["band"])
def scan_few_times():
    saved = {}
    last_network = []
    for n in range(3):
        text = get_wifi_text()
        if text.strip() == "":
            continue
        last_network = read_networks(text)
        for item in last_network:
            if item["name"] == "(hidden)":
                continue
            signal_text = item["signal"].replace("%","").strip()
            if signal_text.isdigit() == False:
                continue
            number = int(signal_text)
            if item["name"] not in saved:
                saved[item["name"]] = []
            saved[item["name"]].append(number)
        if n < 2:
            print("scanning again...")
            time.sleep(2)
    for item in last_network:
        item["jump"] = 0
        if item["name"] not in saved:
            continue
        nums = saved[item["name"]]
        if len(nums) < 2:
            continue
        biggest = nums[0]
        smallest = nums[0]
        for num in nums:
            if num > biggest:
                biggest = num 
            if num < smallest:
                smallest = num
            item["jump"] = biggest-smallest
        ordered = []
        for num in nums:
            ordered.append(num)
        ordered.sort()
        if len(ordered) %2 == 1:
            middle = ordered[len(ordered) // 2]
        else:
            left = ordered[len(ordered) // 2-1]
            right = ordered[len(ordered) // 2]
            middle = (left+right) // 2
        item["signal"] = str(middle) + "%"
    return last_network

def rate_network(item,crowd):
    reasons = []
    score, label = security_score(item["auth"])
    reasons.append(label + " security")
    steady = 10
    steady_reasons = []
    signal_text = item["signal"].replace("%","").strip()
    signal_number = -1
    if signal_text.isdigit():
        signal_number = int(signal_text)
    if signal_number >= 0 and signal_number <40:
        steady = steady-2
        steady_reasons.append("weak signal")
    elif signal_number >= 70:
        steady_reasons.append("strong signal")
    elif signal_number >= 0:
        steady = steady-1
        steady_reasons.append("medium signal")
    band = item["band"].lower()
    if "2.4" in band:
        steady = steady-1
        steady_reasons.append("2.4 GHz is more crowded")
    elif "5" in band:
        steady_reasons.append("5 GHz band")
    others = crowd-1
    if others <0:
        others = 0
    elif others >=3:
        steady = steady-2
        steady_reasons.append("channel is crowded")
    elif others >=1:
        steady = steady-1
        steady_reasons.append("others networks on this channel")
    if item.get("mixed") == True:
        score = score-3
        reasons.append("same name has different security")
    jump = 0
    if "jump" in item:
        jump = item["jump"]
        if jump >= 30:
            steady = steady -2 
            steady_reasons.append("signal jumps around")
        elif jump >= 15:
            steady = steady-1
            steady_reasons.append("signal moves a bit")
    if score <0:
        score=0
    if score >10:
        score=10
    if steady <0:
        steady=0
    if steady>10:
        steady=10
    final = score
    if steady < score:
        final = steady
    return final,score,steady,reasons,steady_reasons
def show_networks(networks):
    mark_mixed_names(networks)
    print("Found", len(networks), "network(s)")
    print("")
    for item in networks:
        crowd = count_on_channel(networks, item["channel"])
        final,score,steady,reasons,steady_reasons = rate_network(item,crowd)
        item["final"] = final
    for i in range(len(networks)):
        for j in range(len(networks)-1):
            if networks[j]["final"] > networks[j+1]["final"]:
                temp = networks[j]
                networks[j] = networks[j+1]
                networks[j+1] = temp
    for item in networks:
        crowd = count_on_channel(networks, item["channel"])
        final,score,steady, reasons, steady_reasons = rate_network(item, crowd)
        print(item["name"])
        print(" score: ",str(final)+ "/10")
        print(" security score : ",str(score)+ "/10")
        print(" stability score : ",str(steady)+ "/10")
        print( "signal: ", item["signal"])
        jump = 0
        if "jump" in item:
            jump = item["jump"]
        print(" jump: ", str(jump)+"%")
        print(" channel: ", item["channel"])
        print(" band: ", item["band"])
        print(" why: ")
        for reason in reasons:
            print("  security: ", reason)
        for reason in steady_reasons:
            print("  stability :", reason)
        print("--------------------")
print("scanning a few times...")
networks = scan_few_times()
if len(networks) == 0:
    print("No networks found")
else:
    show_networks(networks) 
    show_channels(networks)