import requests
import re
from datetime import date, timedelta
import csv
import os

# ------------------- Fetch Miami Climate Report -------------------
def fetch_mia_climate_report():
    url = "https://forecast.weather.gov/product.php?site=MFL&issuedby=MIA&product=CLI&format=CI&version=1&glossary=0"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    lines = r.text.splitlines()

    data = {
        "date": None,
        "high_temp": None,
        "high_temp_time": "",
        "low_temp": None,
        "low_temp_time": "",
        "precip": "0.00",
        "mean_wind_speed": None,
        "highest_wind_speed": None,
        "highest_wind_dir": None
    }

    # Extract report date
    for line in lines:
        m = re.search(r"THE MIAMI CLIMATE SUMMARY FOR (\w+ \d{1,2} \d{4})", line)
        if m:
            report_date = date.today().strftime("%Y-%m-%d")
            data["date"] = report_date
            break

    # Parse observed section
    observed_section = True
    prev_line = ""
    for line in lines:
        if any(keyword in line for keyword in ["CLIMATE NORMALS", "SUNRISE", "SUNSET",
                                               "-  INDICATES", "R  INDICATES",
                                               "MM INDICATES", "T  INDICATES"]):
            observed_section = False
        if not observed_section:
            break

        # MAXIMUM temp and time
        if "MAXIMUM" in line:
            m = re.search(r"MAXIMUM\s+(\d+)\s+(\d{1,2}:\d{2}\s*[AP]M)", line)
            if m:
                data["high_temp"] = int(m.group(1))
                data["high_temp_time"] = m.group(2).strip()

        # MINIMUM temp and time
        if "MINIMUM" in line:
            m = re.search(r"MINIMUM\s+(\d+)\s+(\d{1,2}:\d{2}\s*[AP]M)", line)
            if m:
                data["low_temp"] = int(m.group(1))
                data["low_temp_time"] = m.group(2).strip()

        # PRECIPITATION
        if "PRECIPITATION" in prev_line and line.strip().startswith("YESTERDAY"):
             m = re.search(r"YESTERDAY\s+([\d.]+)", line)
             if m:
                 data["precip"] = f"{float(m.group(1)):.2f}"

        # Wind
        if "AVERAGE WIND SPEED" in line:
            m = re.search(r"AVERAGE WIND SPEED\s+([\d.]+)", line)
            if m:
                data["mean_wind_speed"] = float(m.group(1))
        if "HIGHEST WIND SPEED" in line:
            m = re.search(r"HIGHEST WIND SPEED\s+(\d+)", line)
            if m:
                data["highest_wind_speed"] = int(m.group(1))
        if "HIGHEST WIND DIRECTION" in line:
            m = re.search(r"HIGHEST WIND DIRECTION\s+([A-Z]+) \((\d+)\)", line)
            if m:
                data["highest_wind_dir"] = int(m.group(2))

        prev_line = line
    return data

# ------------------- Fetch Sounding Data -------------------
def fetch_sounding(station="MFL", yymmdd="251113", cycle="18"):
    url = f"https://www.spc.noaa.gov/exper/soundings/{yymmdd}{cycle}_OBS/{station}.txt"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        print(f"Sounding {yymmdd}{cycle} not available. HTTP {r.status_code}")
        return None

    lines = r.text.splitlines()
    h1000 = h850 = temp500 = pw_inches = None

    for line in lines:
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) >= 6:
            p = float(parts[0])
            h = float(parts[1])
            t = float(parts[2])
            if abs(p - 1000.0) < 1:
                h1000 = h
            if abs(p - 850.0) < 1:
                h850 = h
            if abs(p - 500.0) < 1:
                temp500 = t
        if "Precip Water" in line:
            m = re.search(r"Precip Water:\s*([\d.]+)\s*in", line)
            if m:
                pw_inches = float(m.group(1))

    thickness = round(h850 - h1000, 1) if h1000 is not None and h850 is not None else None

    return {
        "thickness_1000_850": thickness,
        "temp_500mb": temp500,
        "pw_inches": pw_inches
    }

# ------------------- MAIN EXECUTION -------------------
today = date.today()
yesterday = today - timedelta(days=1)

station = "MFL"
y = yesterday.year % 100
m = yesterday.month
d = yesterday.day
yymmdd_yesterday = f"{y:02d}{m:02d}{d:02d}"
yymmdd_today = f"{today.year % 100:02d}{today.month:02d}{today.day:02d}"

# Fetch soundings
snd_18 = fetch_sounding(station, yymmdd_yesterday, "18")  # yesterday 18Z
snd_00 = fetch_sounding(station, yymmdd_today, "00")      # today 00Z

# Average sounding data
def avg_val(key):
    vals = []
    for snd in [snd_18, snd_00]:
        if snd and snd.get(key) is not None:
            vals.append(snd[key])
    return round(sum(vals)/len(vals), 2) if vals else None

thick = avg_val("thickness_1000_850")
avg_thickness = round(thick) if thick is not None else None
avg_t500 = avg_val("temp_500mb")
avg_pw = avg_val("pw_inches")

# Fetch Miami climate report
cli = fetch_mia_climate_report()

# Build row for yesterday
row = {
    "date": yesterday.isoformat(),
    "thickness_1000_850": avg_thickness,
    "temp_500mb": avg_t500,
    "pw_inches": f"{avg_pw:.2f}" if avg_pw is not None else "",
    "high_temp": cli.get("high_temp"),
    "high_temp_time": cli.get("high_temp_time", ""),
    "low_temp": cli.get("low_temp"),
    "low_temp_time": cli.get("low_temp_time", ""),
    "precip": cli.get("precip"),
    "mean_wind_speed": cli.get("mean_wind_speed"),
    "highest_wind_speed": cli.get("highest_wind_speed"),
    "highest_wind_dir": cli.get("highest_wind_dir"),
    "remark": ""  # keep empty or let other script fill
}

# ------------------- Save to CSV -------------------
csv_path = "../data/processed/daily_upperair_climate.csv"
fieldnames = [
    "date",
    "thickness_1000_850",
    "temp_500mb",
    "pw_inches",
    "high_temp",
    "high_temp_time",
    "low_temp",
    "low_temp_time",
    "precip",
    "mean_wind_speed",
    "highest_wind_speed",
    "highest_wind_dir",
    "remark"
]

file_exists = os.path.exists(csv_path)

with open(csv_path, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    writer.writerow(row)
