import requests


ICE_THICKNESS_YEAR_URL = "https://www.weather.gov/source/aprfc/it_2026.json"
ICE_THICKNESS_EXTRA_URL = "https://www.weather.gov/source/aprfc/it_extra.json"


def get_ice_thickness_dataset_dropdown():
    return [
        {"label": "Current Season / 2026", "value": "current"},
        {"label": "Historical / Extra", "value": "extra"},
    ]


def get_ice_thickness_month_dropdown():
    return [
        {"label": "All months", "value": "all"},
        {"label": "January", "value": "01"},
        {"label": "February", "value": "02"},
        {"label": "March", "value": "03"},
        {"label": "April", "value": "04"},
        {"label": "May", "value": "05"},
        {"label": "June", "value": "06"},
        {"label": "July", "value": "07"},
        {"label": "August", "value": "08"},
        {"label": "September", "value": "09"},
        {"label": "October", "value": "10"},
        {"label": "November", "value": "11"},
        {"label": "December", "value": "12"},
    ]


def fetch_json(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def collect_ice_features_from_geojson_like(data, month="all"):

    features = []

    if isinstance(data, dict) and data.get("type") == "FeatureCollection":
        features.extend(data.get("features", []))

    if isinstance(data, dict):

        for year_key, year_obj in data.items():

            if not isinstance(year_obj, dict):
                continue

            if year_obj.get("type") == "FeatureCollection":
                features.extend(year_obj.get("features", []))

            months = year_obj.get("months", {})

            if isinstance(months, dict):

                for month_key, month_obj in months.items():

                    if month != "all" and month_key != month:
                        continue

                    if (
                        isinstance(month_obj, dict)
                        and month_obj.get("type") == "FeatureCollection"
                    ):
                        features.extend(month_obj.get("features", []))

    clean_features = []

    for feature in features:

        geom = feature.get("geometry")
        props = feature.get("properties", {})

        if not geom:
            continue

        name = props.get("name", "Ice Thickness Site")

        data_rows = props.get("data", [])

        latest_date = ""
        latest_thickness = ""

        if data_rows and isinstance(data_rows, list):

            latest = data_rows[-1]

            if isinstance(latest, list) and len(latest) >= 2:
                latest_date = latest[0]
                latest_thickness = latest[1]

        snow_depth = props.get("snowDepth", "")
        notes = props.get("publicNotes", "")

        feature["properties"] = {
            "name": name,
            "latest_date": latest_date,
            "ice_thickness": latest_thickness,
            "snow_depth": snow_depth,
            "notes": notes,
            "label": str(latest_thickness) if latest_thickness else "",
        }

        clean_features.append(feature)

    return {
        "type": "FeatureCollection",
        "crs": {"properties": {"name": "EPSG:4326"}},
        "features": clean_features,
    }


def fetch_ice_thickness_geojson(dataset="current", month="all"):

    url = (
        ICE_THICKNESS_YEAR_URL
        if dataset == "current"
        else ICE_THICKNESS_EXTRA_URL
    )

    data = fetch_json(url)

    return collect_ice_features_from_geojson_like(
        data,
        month=month,
    )
    
# ============================================================
# WATER TEMPERATURE
# ============================================================

import requests


WATER_TEMPERATURE_URL = "https://www.weather.gov/source/aprfc/tw.json"


def fetch_aprfc_water_temperature_geojson():
    response = requests.get(WATER_TEMPERATURE_URL, timeout=30)
    response.raise_for_status()

    raw_geojson = response.json()

    features = []

    for feature in raw_geojson.get("features", []):

        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        props = feature.get("properties", {})

        # Skip invalid geometries
        if geometry.get("type") != "Point" or len(coords) < 2:
            continue

        # Safe coordinate parsing
        try:
            lon = float(coords[0])
            lat = float(coords[1])
        except Exception:
            continue

        # Latest water temperature value
        data = props.get("data", [])
        latest_value = "N/A"

        if data:
            latest_row = data[-1]

            if isinstance(latest_row, list) and len(latest_row) >= 2:
                latest_value = str(latest_row[1])

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
                    "owner": str(props.get("owner", "N/A")),
                    "elev": str(props.get("elev", "N/A")),
                    "tw": latest_value,
                    "label": f"{latest_value}°",
                },
            }
        )

    print(
        f"[APRFCWaterTemperatureViewer] "
        f"Clean features: {len(features)}"
    )

    return {
        "type": "FeatureCollection",
        "crs": {
            "properties": {
                "name": "EPSG:4326"
            }
        },
        "features": features,
    }
    
    
# ============================================================
# ICE THICKNESS
# ============================================================

import requests


ICE_THICKNESS_EXTRA_URL = "https://www.weather.gov/source/aprfc/it_extra.json"
ICE_THICKNESS_YEAR_URL_TEMPLATE = (
    "https://www.weather.gov/source/aprfc/it_{year}.json"
)


ICE_THICKNESS_MONTH_OPTIONS = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "11": "November",
    "12": "December",
}


ICE_THICKNESS_YEAR_OPTIONS = {
    str(year): str(year)
    for year in range(1931, 2027)
}


ICE_THICKNESS_PRODUCT_OPTIONS = {
    "ice": "Ice Thickness",
    "percent_avg": "Ice Thickness % Avg",
}


def get_ice_thickness_month_dropdown():
    return [
        {"label": label, "value": month}
        for month, label in ICE_THICKNESS_MONTH_OPTIONS.items()
    ]


def get_ice_thickness_year_dropdown():
    return [
        {"label": label, "value": year}
        for year, label in ICE_THICKNESS_YEAR_OPTIONS.items()
    ]


def get_ice_thickness_product_dropdown():
    return [
        {"label": label, "value": product}
        for product, label in ICE_THICKNESS_PRODUCT_OPTIONS.items()
    ]


def get_ice_color(value):
    try:
        value = float(value)
    except Exception:
        return "#999999"

    if value < 5:
        return "#ff0000"
    if value < 10:
        return "#ff9900"
    if value < 20:
        return "#ffff00"
    if value < 30:
        return "#66ff00"
    if value < 40:
        return "#00cc00"
    if value < 50:
        return "#00ccff"
    if value < 75:
        return "#0033cc"
    return "#ff00ff"


def get_percent_avg_color(value):
    try:
        value = float(value)
    except Exception:
        return "#999999"

    if value < 25:
        return "#ff0000"
    if value < 50:
        return "#ff9900"
    if value < 75:
        return "#ffff00"
    if value < 100:
        return "#99ff33"
    if value < 125:
        return "#00cc00"
    if value < 150:
        return "#00ccff"
    if value < 175:
        return "#3366ff"
    if value < 200:
        return "#6633cc"
    return "#9900cc"


def fetch_ice_json_for_year(year):
    year = str(year)

    if year == "2026":
        url = ICE_THICKNESS_YEAR_URL_TEMPLATE.format(year=year)
    else:
        url = ICE_THICKNESS_EXTRA_URL

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_aprfc_ice_thickness_geojson(
    month="03",
    year="2026",
    product="ice",
):
    month = str(month).zfill(2)
    year = str(year)
    product = str(product)

    raw_json = fetch_ice_json_for_year(year)

    if year == "2026":
        month_data = raw_json.get("months", {}).get(month, {})
    else:
        month_data = (
            raw_json
            .get("years", {})
            .get(year, {})
            .get("months", {})
            .get(month, {})
        )

    raw_features = month_data.get("features", [])
    features = []

    for feature in raw_features:
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
        latest_date = "N/A"
        ice_value = None

        if data:
            latest_row = data[-1]
            if isinstance(latest_row, list) and len(latest_row) >= 2:
                latest_date = str(latest_row[0])
                try:
                    ice_value = float(latest_row[1])
                except Exception:
                    ice_value = None

        averages = props.get("averages") or {}
        avg_info = averages.get(month, {}) or {}
        avg_value = avg_info.get("avg")
        avg_count = avg_info.get("num", "N/A")

        percent_avg = None
        if ice_value is not None and avg_value not in (None, 0, "0", "N/A"):
            try:
                avg_float = float(avg_value)
                if avg_float > 0:
                    percent_avg = (ice_value / avg_float) * 100
            except Exception:
                percent_avg = None

        if product == "percent_avg":
            display_value = (
                f"{percent_avg:.0f}" if percent_avg is not None else "N/A"
            )
            label = f"{display_value}%"
            color = get_percent_avg_color(percent_avg)
        else:
            display_value = (
                f"{ice_value:.0f}" if ice_value is not None else "N/A"
            )
            label = f'{display_value}"'
            color = get_ice_color(ice_value)

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
                    "year": year,
                    "month": month,
                    "date": latest_date,
                    "ice": (
                        f"{ice_value:.0f}"
                        if ice_value is not None else "N/A"
                    ),
                    "avg": str(avg_value) if avg_value is not None else "N/A",
                    "avg_count": str(avg_count),
                    "percent_avg": (
                        f"{percent_avg:.0f}"
                        if percent_avg is not None else "N/A"
                    ),
                    "label": label,
                    "color": color,
                },
            }
        )

    print(
        f"[APRFCIceThicknessViewer] "
        f"year={year}, month={month}, product={product}, "
        f"features={len(features)}"
    )

    return {
        "type": "FeatureCollection",
        "crs": {"properties": {"name": "EPSG:4326"}},
        "features": features,
    }
    
    
# ============================================================
# BREAKUP DATES RIVER VIEW
# ============================================================

import requests
from datetime import datetime


BREAKUP_DATA_URL = "https://www.weather.gov/source/aprfc/breakupData.json"

BREAKUP_RIVER_OPTIONS = {
    "kuskokwim": "Kuskokwim River",
    "yukon": "Yukon River",
}

BREAKUP_RIVERS = {
    "kuskokwim": {
        "locations": [281, 276, 286, 285, 284, 273, 270, 274, 288, 269, 271, 278],
        "name": "Kuskokwim River",
        "y_min": 90,
        "y_max": 161,
    },
    "yukon": {
        "locations": [468, 469, 465, 472, 494, 491, 475, 480, 478, 471],
        "name": "Yukon River",
        "y_min": 90,
        "y_max": 161,
    },
}


def get_breakup_river_dropdown():
    return [{"label": label, "value": key} for key, label in BREAKUP_RIVER_OPTIONS.items()]


def get_breakup_year_dropdown():
    current_year = datetime.utcnow().year
    return [{"label": str(year), "value": str(year)} for year in range(1980, current_year + 1)]


def fetch_breakup_data():
    response = requests.get(BREAKUP_DATA_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def percentile(values, pct):
    values = sorted(values)
    if not values:
        return None

    k = (len(values) - 1) * pct
    f = int(k)
    c = min(f + 1, len(values) - 1)

    if f == c:
        return values[f]

    return values[f] + (values[c] - values[f]) * (k - f)


def jday_to_label(jday):
    try:
        date = datetime.strptime(f"2001 {int(round(jday))}", "%Y %j")
        return date.strftime("%b %-d")
    except Exception:
        try:
            date = datetime.strptime(f"2001 {int(round(jday))}", "%Y %j")
            return date.strftime("%b %#d")
        except Exception:
            return str(jday)


def build_breakup_boxplot_figure(
    river="kuskokwim",
    normals_start_year="1980",
    normals_end_year="2025",
    year_to_plot="2026",
):
    all_data = fetch_breakup_data()
    current_year = datetime.utcnow().year

    normals_start_year = int(normals_start_year or 1980)
    normals_end_year = int(normals_end_year or current_year - 1)
    year_to_plot = int(year_to_plot or current_year)

    river_cfg = BREAKUP_RIVERS.get(river, BREAKUP_RIVERS["kuskokwim"])

    site_names = []
    q1_values = []
    median_values = []
    q3_values = []
    lower_values = []
    upper_values = []
    year_x = []
    year_y = []

    for site_id in river_cfg["locations"]:
        site_key = str(site_id)

        if site_key not in all_data:
            print(f"[Breakup River View] Missing site: {site_key}")
            continue

        site = all_data[site_key]
        hdata = site.get("hdata", [])
        series = []

        for row in hdata:
            if not isinstance(row, list) or len(row) < 2:
                continue

            try:
                row_year = int(row[0])
                row_jday = float(row[1])
            except Exception:
                continue

            if normals_start_year <= row_year <= normals_end_year:
                series.append([row_year, row_jday])

        jdays = [row[1] for row in series]

        if not jdays:
            continue

        site_index = len(site_names)
        site_name = site.get("location", site_key)

        site_names.append(f"{site_name} ({len(jdays)})")

        lower_values.append(min(jdays))
        median = percentile(jdays, 0.50)
        q1_raw = percentile(jdays, 0.25)
        q3_raw = percentile(jdays, 0.75)
        iqr = q3_raw - q1_raw

        q1_values.append(median - iqr / 2)
        median_values.append(median)
        q3_values.append(median + iqr / 2)
        upper_values.append(max(jdays))

        compare_record = site.get("data", {}).get(str(year_to_plot))

        if compare_record and "jday" in compare_record:
            try:
                year_x.append(site_index)
                year_y.append(float(compare_record["jday"]))
            except Exception:
                pass

    y_ticks = list(range(river_cfg["y_min"], river_cfg["y_max"] + 1, 7))
    y_labels = [jday_to_label(day) for day in y_ticks]

    print(
        f"[Breakup River View] river={river}, "
        f"normals={normals_start_year}-{normals_end_year}, "
        f"year_to_plot={year_to_plot}, sites={len(site_names)}"
    )

    return {
        "data": [
            {
                "type": "box",
                "name": "Breakup Dates",
                "x": site_names,
                "q1": q1_values,
                "median": median_values,
                "q3": q3_values,
                "lowerfence": lower_values,
                "upperfence": upper_values,
                "boxpoints": False,
                "fillcolor": "rgba(240,240,224,0.85)",
                "line": {
                    "color": "rgb(80,180,255)",
                    "width": 2,
                },
                "marker": {
                    "color": "rgb(80,180,255)",
                },
                "whiskerwidth": 0.5,
            },
            {
                "type": "scatter",
                "mode": "markers",
                "name": f"{year_to_plot} Breakup Date",
                "x": [site_names[i] for i in year_x],
                "y": year_y,
                "marker": {
                    "size": 12,
                    "color": "red",
                    "line": {
                        "color": "red",
                        "width": 1,
                    },
                },
            },
        ],
        "layout": {
            "title": {
                "text": f"<b>{river_cfg['name']} Breakup Dates {normals_start_year} - {normals_end_year}</b>",
                "font": {
                    "size": 22,
                    "family": "Arial",
                },
                "x": 0.5,
            },
            "xaxis": {
                "title": "",
                "tickangle": -45,
                "tickfont": {
                    "size": 13,
                    "family": "Arial",
                    "color": "black",
                },
            },
            "yaxis": {
                "title": {
                    "text": "<b>Breakup Date</b>",
                    "font": {
                        "size": 16,
                        "family": "Arial",
                        "color": "black",
                    },
                },
                "range": [river_cfg["y_min"], river_cfg["y_max"]],
                "tickvals": y_ticks,
                "ticktext": y_labels,
                "tickfont": {
                    "size": 13,
                    "family": "Arial",
                    "color": "black",
                },
                "dtick": 7,
                "gridcolor": "rgba(0,0,0,0.12)",
            },
            "legend": {
                "orientation": "v",
                "x": 1.02,
                "y": 1,
                "font": {
                    "size": 12,
                    "family": "Arial",
                },
            },
            "annotations": [
                {
                    "text": "Dates are normalized to non-leap year values",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0,
                    "y": 1.08,
                    "showarrow": False,
                    "font": {
                        "size": 13,
                        "family": "Arial",
                        "color": "gray",
                    },
                    "xanchor": "left",
                }
            ],
            "margin": {
                "l": 80,
                "r": 130,
                "t": 90,
                "b": 170,
            },
            "height": 620,
            "showlegend": True,
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
        },
    }
    
    
# ============================================================
# APRFC INTERACTIVE BREAKUP MAP
# ============================================================

import requests


APRFC_BREAKUP_BASE = "https://www.weather.gov/source/aprfc"

BREAKUP_RIVER_URL = f"{APRFC_BREAKUP_BASE}/riverStat.json"
BREAKUP_VILLAGE_URL = f"{APRFC_BREAKUP_BASE}/villages.json"
BREAKUP_METADATA_URL = f"{APRFC_BREAKUP_BASE}/metadata.json"


RIVER_STATUS_LABELS = {
    "unknown": "Unknown",
    "mostice": "Mostly Ice",
    "someopen": "Some Open",
    "mostopen": "Mostly Open",
    "open": "Open",
}


VILLAGE_STATUS_LABELS = {
    "none": "No Warning",
    "advise": "Flood Advisory",
    "watch": "Flood Watch",
    "warn": "Flood Warning",
}


def fetch_json(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_aprfc_breakup_river_geojson():
    geojson = fetch_json(BREAKUP_RIVER_URL)

    features = []

    for feature in geojson.get("features", []):
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}

        status = str(props.get("status", "unknown")).lower()
        status_label = RIVER_STATUS_LABELS.get(status, status.title())

        name = (
            props.get("NAMEEN")
            or props.get("nameen")
            or props.get("Name")
            or props.get("name")
            or "River Segment"
        )

        feature["properties"] = {
            **props,
            "display_name": str(name),
            "status": status,
            "status_label": status_label,
        }

        if geom:
            features.append(feature)

    print(f"[APRFCInteractiveBreakupMapViewer] River features: {len(features)}")

    return {
        "type": "FeatureCollection",
        "crs": {"properties": {"name": "EPSG:4326"}},
        "features": features,
    }


def fetch_aprfc_breakup_village_geojson():
    geojson = fetch_json(BREAKUP_VILLAGE_URL)

    features = []

    for feature in geojson.get("features", []):
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}

        status = str(props.get("status", "none")).lower()
        status_label = VILLAGE_STATUS_LABELS.get(status, status.title())

        name = props.get("name") or props.get("Name") or "Community"

        feature["properties"] = {
            **props,
            "display_name": str(name),
            "village_status": status,
            "village_status_label": status_label,
        }

        if geom:
            features.append(feature)

    print(f"[APRFCInteractiveBreakupMapViewer] Village features: {len(features)}")

    return {
        "type": "FeatureCollection",
        "crs": {"properties": {"name": "EPSG:4326"}},
        "features": features,
    }


def fetch_aprfc_breakup_metadata():
    try:
        metadata = fetch_json(BREAKUP_METADATA_URL)
        meta = metadata.get("metadata", {})
        return {
            "forecaster": str(meta.get("forecaster", "N/A")),
            "notes": str(meta.get("notes", "N/A")),
            "last_update": str(meta.get("lastUpdate", "N/A")),
        }
    except Exception:
        return {
            "forecaster": "N/A",
            "notes": "N/A",
            "last_update": "N/A",
        }
        
        
# ============================================================
# HISTORIC BREAKUP DATES DATABASE
# ============================================================

import requests
from datetime import datetime


BREAKUP_DATA_URL = "https://www.weather.gov/source/aprfc/breakupData.json"


def fetch_breakup_data():
    response = requests.get(BREAKUP_DATA_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def get_breakup_site_dropdown():
    data = fetch_breakup_data()

    options = []
    for site_id, site in data.items():
        label = site.get("name") or site.get("location") or f"Site {site_id}"
        options.append({"label": f"{label} ({site_id})", "value": str(site_id)})

    return sorted(options, key=lambda x: x["label"])


def jday_to_label(jday):
    try:
        date = datetime.strptime(f"2013 {int(round(jday))}", "%Y %j")
        return date.strftime("%b %-d")
    except Exception:
        try:
            date = datetime.strptime(f"2013 {int(round(jday))}", "%Y %j")
            return date.strftime("%b %#d")
        except Exception:
            return str(jday)


def percentile(values, pct):
    values = sorted(values)

    if not values:
        return None

    k = (len(values) - 1) * pct
    f = int(k)
    c = min(f + 1, len(values) - 1)

    if f == c:
        return values[f]

    return values[f] + (values[c] - values[f]) * (k - f)


def build_trend_line(points):
    """
    Build one APRFC-style regression trend line for selected/statistical period.
    """
    if len(points) < 2:
        return [], []

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)

    denom = sum((x - x_mean) ** 2 for x in xs)

    if denom == 0:
        return [], []

    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
    intercept = y_mean - slope * x_mean

    trend_x = [min(xs), max(xs)]
    trend_y = [
        slope * trend_x[0] + intercept,
        slope * trend_x[1] + intercept,
    ]

    return trend_x, trend_y


def build_breakup_database_figure(site_id="17", start_year="1980", end_year=None):
    data = fetch_breakup_data()

    site_id = str(site_id)
    if site_id not in data:
        raise ValueError(f"Site ID {site_id} not found in breakupData.json")

    site = data[site_id]
    site_name = site.get("name", f"Site {site_id}")

    current_year = datetime.utcnow().year
    start_year = int(start_year or 1980)
    end_year = int(end_year or current_year)

    hdata = site.get("hdata", [])

    all_points = []
    stats_points = []

    for row in hdata:
        if not isinstance(row, list) or len(row) < 2:
            continue

        try:
            year = int(row[0])
            jday = float(row[1])
        except Exception:
            continue

        all_points.append([year, jday])

        if start_year <= year <= end_year:
            stats_points.append([year, jday])

    stat_values = [p[1] for p in stats_points]

    if stat_values:
        min_v = min(stat_values)
        max_v = max(stat_values)
        median_v = percentile(stat_values, 0.5)

        q1_raw = percentile(stat_values, 0.25)
        q3_raw = percentile(stat_values, 0.75)
        iqr = q3_raw - q1_raw

        q1_v = median_v - iqr / 2
        q3_v = median_v + iqr / 2
    else:
        min_v = max_v = median_v = q1_v = q3_v = None

    trend_x, trend_y = build_trend_line(stats_points)

    stats_plot_year = current_year + 7
    x_max = current_year + 12

    y_ticks = list(range(85, 171, 7))
    y_labels = [jday_to_label(day) for day in y_ticks]

    x_min = min([p[0] for p in all_points]) - 2 if all_points else 1980

    base_shapes = [
        {
            "type": "rect",
            "xref": "x",
            "yref": "paper",
            "x0": start_year,
            "x1": end_year - 0.5,
            "y0": 0,
            "y1": 1,
            "fillcolor": "rgba(180,220,170,0.45)",
            "line": {"width": 0},
            "layer": "below",
        },
        {
            "type": "line",
            "xref": "x",
            "yref": "paper",
            "x0": end_year,
            "x1": end_year,
            "y0": 0,
            "y1": 1,
            "line": {"color": "orange", "width": 2, "dash": "dash"},
        },
    ]

    box_x = stats_plot_year
    box_width = 1.6

    if min_v is not None:
        stats_box_shapes = [
            {
                "type": "line",
                "xref": "x",
                "yref": "y",
                "x0": box_x,
                "x1": box_x,
                "y0": min_v,
                "y1": max_v,
                "line": {"color": "blue", "width": 2},
            },
            {
                "type": "line",
                "xref": "x",
                "yref": "y",
                "x0": box_x - box_width / 2,
                "x1": box_x + box_width / 2,
                "y0": min_v,
                "y1": min_v,
                "line": {"color": "blue", "width": 2},
            },
            {
                "type": "line",
                "xref": "x",
                "yref": "y",
                "x0": box_x - box_width / 2,
                "x1": box_x + box_width / 2,
                "y0": max_v,
                "y1": max_v,
                "line": {"color": "blue", "width": 2},
            },
            {
                "type": "rect",
                "xref": "x",
                "yref": "y",
                "x0": box_x - box_width / 2,
                "x1": box_x + box_width / 2,
                "y0": q1_v,
                "y1": q3_v,
                "fillcolor": "rgba(240,240,240,0.85)",
                "line": {"color": "black", "width": 1},
            },
            {
                "type": "line",
                "xref": "x",
                "yref": "y",
                "x0": box_x - box_width / 2,
                "x1": box_x + box_width / 2,
                "y0": median_v,
                "y1": median_v,
                "line": {"color": "blue", "width": 3},
            },
        ]
    else:
        stats_box_shapes = []

    stats_text = (
        f"<b>Statistics</b><br>"
        f"Start Year: {start_year}<br>"
        f"End Year: {end_year}<br>"
        f"Number: {len(stats_points)}/{end_year - start_year + 1}<br>"
        f"Min: {jday_to_label(min_v) if min_v is not None else 'N/A'}<br>"
        f"Median: {jday_to_label(median_v) if median_v is not None else 'N/A'}<br>"
        f"Max: {jday_to_label(max_v) if max_v is not None else 'N/A'}<br>"
        f"IQR: {(q3_v - q1_v):.1f} days"
        if q1_v is not None
        else "<b>Statistics</b><br>No data"
    )

    return {
        "data": [
            {
                "type": "scatter",
                "mode": "markers",
                "name": "Breakup Dates",
                "x": [p[0] for p in all_points],
                "y": [p[1] for p in all_points],
                "marker": {
                    "size": 8,
                    "color": "white",
                    "line": {"color": "black", "width": 2},
                },
            },
            {
                "type": "scatter",
                "mode": "lines",
                "name": "Trend",
                "x": trend_x,
                "y": trend_y,
                "line": {
                    "color": "green",
                    "width": 2,
                    "dash": "dot",
                },
            },
            {
                "type": "scatter",
                "mode": "markers",
                "name": "Outliers",
                "x": [None],
                "y": [None],
                "marker": {
                    "size": 8,
                    "color": "white",
                    "line": {"color": "red", "width": 2},
                },
            },
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Min,25%,Median,75%,Max",
                "x": [None],
                "y": [None],
                "line": {"color": "blue", "width": 2},
                "marker": {"size": 10, "color": "blue"},
            },
        ],
        "layout": {
            "title": {"text": f"<b>{site_name}</b>", "x": 0.5},
            "xaxis": {
                "title": "",
                "range": [x_min, x_max],
            },
            "yaxis": {
                "title": "Breakup Date",
                "tickvals": y_ticks,
                "ticktext": y_labels,
            },
            "shapes": base_shapes + stats_box_shapes,
            "annotations": [
                {
                    "text": stats_text,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 1.03,
                    "y": 0.95,
                    "showarrow": False,
                    "align": "left",
                    "bordercolor": "black",
                    "borderwidth": 1,
                    "bgcolor": "white",
                }
            ],
            "margin": {"l": 80, "r": 230, "t": 70, "b": 90},
            "height": 520,
            "showlegend": True,
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
        },
    }