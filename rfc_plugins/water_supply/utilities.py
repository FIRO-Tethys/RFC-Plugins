# ============================================================
# APRFC NRCS SWE MAP
# ============================================================

import requests
from datetime import datetime, timezone


APRFC_NRCS_SWE_URL = "https://www.weather.gov/source/aprfc/nrcs_swe.json"


SWE_PRODUCT_OPTIONS = {
    "swe": "SWE",
    "percent_normal": "SWE % Normal",
}


def get_swe_product_dropdown():
    return [
        {"label": label, "value": key}
        for key, label in SWE_PRODUCT_OPTIONS.items()
    ]


def format_aprfc_date(raw_time):
    try:
        return datetime.fromtimestamp(
            raw_time / 1000,
            tz=timezone.utc,
        ).strftime("%a %b %d %Y")
    except Exception:
        return str(raw_time)


def get_latest_valid_row(rows):
    valid_rows = [
        row for row in rows
        if isinstance(row, list)
        and len(row) >= 2
        and row[1] not in (None, "", "M", "N/A")
    ]

    if not valid_rows:
        return None

    return max(valid_rows, key=lambda row: row[0])


def get_swe_category(value):
    try:
        value = float(value)
    except Exception:
        return "No Data"

    if value >= 50:
        return "50+ in"
    if value >= 43.75:
        return "43.75–50 in"
    if value >= 37.5:
        return "37.5–43.75 in"
    if value >= 31.25:
        return "31.25–37.5 in"
    if value >= 25:
        return "25–31.25 in"
    if value >= 18.75:
        return "18.75–25 in"
    if value >= 12.5:
        return "12.5–18.75 in"
    if value >= 6.25:
        return "6.25–12.5 in"
    return "0–6.25 in"


def get_swe_percent_category(value):
    try:
        value = float(value)
    except Exception:
        return "No Data"

    if value >= 200:
        return "200+%"
    if value >= 175:
        return "175–200%"
    if value >= 150:
        return "150–175%"
    if value >= 125:
        return "125–150%"
    if value >= 100:
        return "100–125%"
    if value >= 75:
        return "75–100%"
    if value >= 50:
        return "50–75%"
    if value >= 25:
        return "25–50%"
    return "0–25%"


def fetch_aprfc_nrcs_swe_geojson(product="swe"):
    response = requests.get(APRFC_NRCS_SWE_URL, timeout=30)
    response.raise_for_status()
    raw_geojson = response.json()

    features = []

    for feature in raw_geojson.get("features", []):
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        props = feature.get("properties", {})

        if geometry.get("type") != "Point" or len(coords) < 2:
            continue

        try:
            lon = float(coords[0])
            lat = float(coords[1])
        except Exception:
            continue

        data = props.get("data", [])
        pct = props.get("pct", [])
        avg = props.get("avg", [])

        latest_date = "N/A"
        latest_swe = None
        latest_pct = None
        latest_avg = None

        latest_data_row = get_latest_valid_row(data)
        if latest_data_row:
            latest_date = format_aprfc_date(latest_data_row[0])
            latest_swe = float(latest_data_row[1])

        latest_pct_row = get_latest_valid_row(pct)
        if latest_pct_row:
            latest_pct = float(latest_pct_row[1])

        latest_avg_row = get_latest_valid_row(avg)
        if latest_avg_row:
            latest_avg = float(latest_avg_row[1])

        if product == "percent_normal":
            value = latest_pct
            label = f"{value:.0f}%" if value is not None else "N/A"
            category = get_swe_percent_category(value)
        else:
            value = latest_swe
            label = f'{value:.1f}"' if value is not None else "N/A"
            category = get_swe_category(value)

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "name": str(props.get("name", "Unknown")),
                    "lid": str(props.get("lid", "N/A")),
                    "elev": str(props.get("elev", "N/A")),
                    "date": latest_date,
                    "swe": f"{latest_swe:.1f}" if latest_swe is not None else "N/A",
                    "pct": f"{latest_pct:.0f}" if latest_pct is not None else "N/A",
                    "avg": f"{latest_avg:.1f}" if latest_avg is not None else "N/A",
                    "label": label,
                    "category": category,
                },
            }
        )

    print(
        f"[APRFCNRCSSWEDataViewer] product={product}, "
        f"features={len(features)}"
    )

    return {
        "type": "FeatureCollection",
        "crs": {"properties": {"name": "EPSG:4326"}},
        "features": features,
    }