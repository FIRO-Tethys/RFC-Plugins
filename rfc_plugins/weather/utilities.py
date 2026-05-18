from datetime import datetime, timedelta, timezone
import requests
import re


# ============================================================
# RFC CONFIG
# ============================================================

RFC_OPTIONS = {
    "APRFC": "Alaska RFC",
}


# ============================================================
# GOES SATELLITE CONFIG + HELPERS
# ============================================================

GOES_PRODUCT_OPTIONS = {
    "GEOCOLOR": "GeoColor",
    "AirMass": "Air Mass RGB",
    "Sandwich": "Sandwich RGB",
    "DayNightCloudMicroCombo": "Day Night Cloud Micro Combo RGB",
    "Dust": "Dust RGB",
    "FireTemperature": "Fire Temperature RGB",
    "01": "1 - Visible: blue",
    "02": "2 - Visible: red",
    "03": '3 - Near IR: "Veggie"',
    "04": "4 - Near IR: cirrus",
    "05": "5 - Near IR: snow/ice",
    "06": "6 - Near IR: cloud particle",
    "07": "7 - IR: shortwave",
    "08": "8 - IR: water vapor - upper",
    "09": "9 - IR: water vapor - mid",
    "10": "10 - IR: water vapor - lower",
    "11": "11 - IR: cloud-top phase",
    "12": "12 - IR: ozone",
    "13": "13 - IR: clean longwave",
    "14": "14 - IR: longwave",
    "15": "15 - IR: dirty longwave",
    "16": "16 - IR: CO₂ longwave",
}

RFC_GOES_CONFIG = {
    "APRFC": {
        "sat_cdn": "GOES18",
        "sector": "ak",
    },
}


def get_rfc_dropdown():
    return [{"label": label, "value": key} for key, label in RFC_OPTIONS.items()]


def get_product_dropdown():
    return [{"label": label, "value": key} for key, label in GOES_PRODUCT_OPTIONS.items()]


def get_frame_dropdown(max_frames_back: int = 240):
    options = [{"label": "0 - Latest", "value": "0"}]

    for i in range(1, max_frames_back + 1):
        total_minutes = i * 10

        if total_minutes < 60:
            label = f"{i} - {total_minutes} min ago"
        else:
            hours = total_minutes / 60
            if hours.is_integer():
                label = f"{i} - {int(hours)} hr ago"
            else:
                label = f"{i} - {hours:.1f} hr ago"

        options.append({"label": label, "value": str(i)})

    return options


def get_goes_config(rfc: str) -> dict:
    return RFC_GOES_CONFIG.get(
        rfc,
        {
            "sat_cdn": "GOES18",
            "sector": "ak",
        },
    )


def floor_to_10_minutes(dt: datetime) -> datetime:
    return dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0)


def build_goes_cdn_image_url(rfc: str, product: str, timestamp: datetime) -> str:
    """
    NOAA STAR CDN filename pattern uses YYYYJJJHHMM, where JJJ is Julian day.

    Example:
    https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/ak/13/
    20261110710_GOES18-ABI-ak-13-1000x1000.jpg
    """
    cfg = get_goes_config(rfc)
    ts = timestamp.strftime("%Y%j%H%M")

    return (
        f"https://cdn.star.nesdis.noaa.gov/{cfg['sat_cdn']}/ABI/SECTOR/"
        f"{cfg['sector']}/{product}/"
        f"{ts}_{cfg['sat_cdn']}-ABI-{cfg['sector']}-{product}-1000x1000.jpg"
    )


def url_exists(url: str, timeout: int = 10) -> bool:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.star.nesdis.noaa.gov/GOES/index.php",
    }

    try:
        r = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        content_type = r.headers.get("Content-Type", "")

        if r.status_code == 200 and "image" in content_type.lower():
            return True

        r = requests.get(url, headers=headers, timeout=timeout, stream=True)
        content_type = r.headers.get("Content-Type", "")

        return r.status_code == 200 and "image" in content_type.lower()

    except requests.RequestException:
        return False


def find_latest_available_timestamp(
    rfc: str,
    product: str,
    max_search_steps: int = 48,
) -> datetime:
    """
    Find the most recent available GOES frame by searching backward
    in 10-minute intervals.
    """
    now_utc = datetime.now(timezone.utc)
    candidate_time = floor_to_10_minutes(now_utc)

    for step in range(max_search_steps):
        ts = candidate_time - timedelta(minutes=10 * step)
        url = build_goes_cdn_image_url(rfc=rfc, product=product, timestamp=ts)

        if url_exists(url):
            return ts

    raise ValueError(
        f"Could not find a recent GOES image for RFC={rfc}, product={product}."
    )


def build_goes_image_url(rfc: str, product: str, frame_back: int = 0) -> str:
    """
    Build a direct image URL for the selected frame_back value.
    frame_back=0 means latest available frame.
    """
    latest_ts = find_latest_available_timestamp(rfc=rfc, product=product)

    target_ts = latest_ts - timedelta(minutes=10 * frame_back)
    target_url = build_goes_cdn_image_url(
        rfc=rfc,
        product=product,
        timestamp=target_ts,
    )

    if url_exists(target_url):
        return target_url

    # Small fallback search in case an intermediate frame is missing
    for extra_step in range(1, 7):
        fallback_ts = target_ts - timedelta(minutes=10 * extra_step)
        fallback_url = build_goes_cdn_image_url(
            rfc=rfc,
            product=product,
            timestamp=fallback_ts,
        )

        if url_exists(fallback_url):
            return fallback_url

    raise ValueError(
        f"Could not find GOES image for RFC={rfc}, "
        f"product={product}, frame_back={frame_back}."
    )


# ============================================================
# RADAR / WEATHER ALERTS CONFIG + HELPERS
# ============================================================

RADAR_REGION_OPTIONS = {
    "APRFC": "Alaska RFC",
}

RADAR_PRODUCT_OPTIONS = {
    "alaska_bref_qcd": "National Radar",
    "local": "Local Radar",
    "alerts": "Weather for a Location / Alerts",
}


def get_radar_region_dropdown():
    return [{"label": label, "value": key} for key, label in RADAR_REGION_OPTIONS.items()]


def get_radar_product_dropdown():
    return [{"label": label, "value": key} for key, label in RADAR_PRODUCT_OPTIONS.items()]


def fetch_radar_stations_geojson():
    url = "https://coast.noaa.gov/arcgis/rest/services/Hosted/WeatherRadarStations/FeatureServer/0/query"

    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
    }

    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        geojson = r.json()
    except Exception as e:
        print(f"Radar station fetch failed: {e}")
        return {"type": "FeatureCollection", "features": []}

    ak_features = []
    for feature in geojson.get("features", []):
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue

        lon, lat = coords[0], coords[1]
        if -180 <= lon <= -130 and 50 <= lat <= 72:
            ak_features.append(feature)

    geojson["features"] = ak_features
    print("Radar station count:", len(ak_features))
    return geojson


def fetch_wwa_arcgis_geojson():
    url = (
        "https://mapservices.weather.noaa.gov/eventdriven/rest/services/WWA/"
        "watch_warn_adv/MapServer/0/query"
    )

    params = {
        "f": "geojson",
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "geometry": "-180,50,-130,72",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        geojson = r.json()

    except Exception as e:
        print(f"WWA ArcGIS query failed: {e}")
        return {
            "type": "FeatureCollection",
            "features": [],
        }

    clean_features = []

    for feature in geojson.get("features", []):

        geom = feature.get("geometry")

        if not geom:
            continue

        geom_type = geom.get("type")

        if geom_type not in [
            "Polygon",
            "MultiPolygon",
            "Point",
            "MultiPoint",
            "LineString",
            "MultiLineString",
        ]:
            continue

        props = feature.get("properties", {})

        headline = (
            props.get("headline")
            or props.get("HEADLINE")
            or props.get("prod_type")
            or props.get("PROD_TYPE")
            or "NWS Alert"
        )

        event = (
            props.get("event")
            or props.get("EVENT")
            or props.get("phenom")
            or props.get("PHENOM")
            or "Alert"
        )

        area = (
            props.get("areaDesc")
            or props.get("AREA_DESC")
            or props.get("name")
            or props.get("NAME")
            or ""
        )

        feature["properties"] = {
            "event": event,
            "headline": headline,
            "areaDesc": area,
        }

        clean_features.append(feature)

    return {
        "type": "FeatureCollection",
        "crs": {"properties": {"name": "EPSG:4326"}},
        "features": clean_features,
    }


def build_selected_location_geojson(
    lon=-151.35,
    lat=60.73,
    name="Selected Location",
):
    return {
        "type": "FeatureCollection",
        "crs": {
            "properties": {
                "name": "EPSG:4326",
            }
        },
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "name": name,
                    "markerColor": "#000000",
                },
            }
        ],
    }
    
def get_latest_hazard_time():
    url = (
        "https://opengeo.ncep.noaa.gov/geoserver/wwa/hazards/ows"
        "?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities"
    )

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        times = re.findall(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z",
            r.text,
        )
        return times[-1] if times else None
    except Exception as e:
        print(f"Hazard time fetch failed: {e}")
        return None
    
    
# ============================================================
# QPE / QPF WMS CONFIG + HELPERS
# ============================================================

RFC_QPE_WMS_URL = (
    "https://mapservices.weather.noaa.gov/raster/services/obs/"
    "rfc_qpe/MapServer/WMSServer"
)

WPC_QPF_WMS_URL = (
    "https://mapservices.weather.noaa.gov/vector/services/precip/"
    "wpc_qpf/MapServer/WMSServer"
)

PRECIP_REGION_OPTIONS = {
    "APRFC": "Alaska RFC",
    "CONUS": "CONUS",
}

PRECIP_VIEW_CONFIG = {
    "APRFC": {"center": [-16500000, 8500000], "zoom": 3.8},
    "CONUS": {"center": [-10700000, 4700000], "zoom": 4.5},
}

PRECIP_DATASET_OPTIONS = {
    "qpe": "QPE - Observed Precipitation",
    "qpf": "QPF - Forecast Precipitation",
}

QPE_PRODUCT_OPTIONS = {
    "last_10d": {
        "label": "Last 10 Days Observed - RFC QPE (inches)",
        "layer": "201",
    },
    "last_7d": {
        "label": "Last 7 Days Observed - RFC QPE (inches)",
        "layer": "205",
    },
    "last_4d": {
        "label": "Last 4 Days Observed - RFC QPE (inches)",
        "layer": "217",
    },
    "last_3d": {
        "label": "Last 3 Days Observed - RFC QPE (inches)",
        "layer": "221",
    },
    "last_2d": {
        "label": "Last 2 Days Observed - RFC QPE (inches)",
        "layer": "225",
    },
    "today_analysis": {
        "label": "Today's Analysis Observed - RFC QPE (inches)",
        "layer": "229",
    },
    "last_24h": {
        "label": "Last 24 Hours Observed - RFC QPE (inches)",
        "layer": "233",
    },
    "since_12z": {
        "label": "Since 12Z Observed - RFC QPE (inches)",
        "layer": "257",
    },
}

# Placeholder QPF layer IDs.
# You need to confirm these from the WPC QPF GetCapabilities XML.
QPF_PRODUCT_OPTIONS = {
    "day_1": {
        "label": "Day 1 QPF",
        "layer": "0",
    },
    "day_2": {
        "label": "Day 2 QPF",
        "layer": "1",
    },
    "day_3": {
        "label": "Day 3 QPF",
        "layer": "2",
    },
}


def get_precip_region_dropdown():
    return [{"label": label, "value": key} for key, label in PRECIP_REGION_OPTIONS.items()]


def get_precip_dataset_dropdown():
    return [{"label": label, "value": key} for key, label in PRECIP_DATASET_OPTIONS.items()]


def get_precip_product_dropdown():
    """
    For now this returns both QPE and QPF options together.
    Later we can make this dynamic based on selected dataset if TethysDash supports dependent dropdowns.
    """
    options = []

    for key, cfg in QPE_PRODUCT_OPTIONS.items():
        options.append({"label": f"QPE: {cfg['label']}", "value": key})

    for key, cfg in QPF_PRODUCT_OPTIONS.items():
        options.append({"label": f"QPF: {cfg['label']}", "value": key})

    return options


def get_precip_wms_url(dataset: str) -> str:
    if dataset == "qpe":
        return RFC_QPE_WMS_URL
    if dataset == "qpf":
        return WPC_QPF_WMS_URL
    raise ValueError(f"Unknown precipitation dataset: {dataset}")


def get_precip_layer_id(dataset: str, product: str) -> str:
    if dataset == "qpe":
        if product not in QPE_PRODUCT_OPTIONS:
            raise ValueError(f"Unknown QPE product: {product}")
        return QPE_PRODUCT_OPTIONS[product]["layer"]

    if dataset == "qpf":
        if product not in QPF_PRODUCT_OPTIONS:
            raise ValueError(f"Unknown QPF product: {product}")
        return QPF_PRODUCT_OPTIONS[product]["layer"]

    raise ValueError(f"Unknown precipitation dataset: {dataset}")


def get_precip_product_label(dataset: str, product: str) -> str:
    if dataset == "qpe":
        return QPE_PRODUCT_OPTIONS[product]["label"]
    if dataset == "qpf":
        return QPF_PRODUCT_OPTIONS[product]["label"]
    return product


# ============================================================
# NDFD FORECAST MAP CONFIG + HELPERS
# ============================================================

import xml.etree.ElementTree as ET


NDFD_REGION_OPTIONS = {
    "APRFC": "Alaska RFC",
}

NDFD_VIEW_CONFIG = {
    "APRFC": {"center": [-16500000, 8500000], "zoom": 3.8},
}

NDFD_PRODUCT_OPTIONS = {
    "qpf": {
        "label": "NDFD Precipitation Forecast",
        "wms_url": "https://mapservices.weather.noaa.gov/geoserver/ndfd/qpf/ows",
        "layer": "qpf",
    },
    "snow": {
        "label": "NDFD Snow Forecast",
        "wms_url": "https://mapservices.weather.noaa.gov/geoserver/ndfd/snow/ows",
        "layer": "snow",
    },
}

NDFD_TIME_OPTIONS = {
    "latest": "Latest available",
    "plus_24": "Around +24 hr",
    "plus_48": "Around +48 hr",
    "plus_72": "Around +72 hr",
    "plus_96": "Around +96 hr",
    "last": "Farthest available",
}


def get_ndfd_region_dropdown():
    return [{"label": label, "value": key} for key, label in NDFD_REGION_OPTIONS.items()]


def get_ndfd_product_dropdown():
    return [
        {"label": cfg["label"], "value": key}
        for key, cfg in NDFD_PRODUCT_OPTIONS.items()
    ]


def get_ndfd_time_dropdown():
    return [
        {"label": label, "value": key}
        for key, label in NDFD_TIME_OPTIONS.items()
    ]


def get_ndfd_product_config(product: str) -> dict:
    if product not in NDFD_PRODUCT_OPTIONS:
        raise ValueError(f"Unknown NDFD product: {product}")
    return NDFD_PRODUCT_OPTIONS[product]


def get_wms_available_times(wms_url: str, layer_name: str):
    caps_url = f"{wms_url}?service=WMS&version=1.3.0&request=GetCapabilities"

    try:
        r = requests.get(caps_url, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        print(f"NDFD GetCapabilities failed: {e}")
        return []

    ns = {"wms": "http://www.opengis.net/wms"}
    times = []

    for layer in root.findall(".//wms:Layer", ns):
        name = layer.find("wms:Name", ns)

        if name is not None and name.text == layer_name:
            for dim in layer.findall("wms:Dimension", ns):
                if dim.attrib.get("name") == "time" and dim.text:
                    times.extend([t.strip() for t in dim.text.split(",") if t.strip()])

    return times


def select_ndfd_time(product: str, time_choice: str):
    cfg = get_ndfd_product_config(product)
    times = get_wms_available_times(cfg["wms_url"], cfg["layer"])

    if not times:
        return None

    if time_choice == "latest":
        return times[0]

    if time_choice == "last":
        return times[-1]

    lead_index_map = {
        "plus_24": 1,
        "plus_48": 2,
        "plus_72": 3,
        "plus_96": 4,
    }

    idx = lead_index_map.get(time_choice, 0)

    if idx >= len(times):
        idx = len(times) - 1

    selected_time = times[idx]
    print(f"NDFD selected time for {product}: {selected_time}")
    print("Available NDFD times:")
    for t in times:
        print(t)

    return selected_time


# ============================================================
# MRMS QPE CONFIG + HELPERS
# ============================================================

MRMS_REGION_OPTIONS = {
    "APRFC": "Alaska RFC",
    "CONUS": "CONUS",
}

MRMS_VIEW_CONFIG = {
    "APRFC": {"center": [-16500000, 8500000], "zoom": 3.8},
    "CONUS": {"center": [-10700000, 4700000], "zoom": 4.5},
}

MRMS_PRODUCT_OPTIONS = {
    "rft_1hr": "MRMS QPE - 1 hour",
    "rft_3hr": "MRMS QPE - 3 hours",
    "rft_6hr": "MRMS QPE - 6 hours",
    "rft_12hr": "MRMS QPE - 12 hours",
    "rft_24hr": "MRMS QPE - 24 hours",
    "rft_48hr": "MRMS QPE - 48 hours",
    "rft_72hr": "MRMS QPE - 72 hours",
}


def get_mrms_region_dropdown():
    return [
        {"label": label, "value": key}
        for key, label in MRMS_REGION_OPTIONS.items()
    ]


def get_mrms_product_dropdown():
    return [
        {"label": label, "value": key}
        for key, label in MRMS_PRODUCT_OPTIONS.items()
    ]
    
# ============================================================
# FREEZING DEGREE DAYS CONFIG + HELPERS
# ============================================================

ACIS_STNDATA_URL = "https://data.rcc-acis.org/StnData"

FDD_REGION_OPTIONS = {
    "APRFC": "Alaska RFC",
}

FDD_VIEW_CONFIG = {
    "APRFC": {"center": [-16500000, 8500000], "zoom": 3.8},
}

# Station set used by APRFC FDD page source
FDD_STATION_OPTIONS = {
    "pacv": "Cordova",
    "panc": "Anchorage",
    "paen": "Kenai",
    "pabr": "Utqiagvik / Barrow",
    "pabe": "Bethel",
    "pabt": "Bettles",
    "pabi": "Delta Junction / Allen AAF",
    "pafa": "Fairbanks",
    "pagk": "Gulkana",
    "pajn": "Juneau",
    "pakn": "King Salmon",
    "padq": "Kodiak",
    "paot": "Kotzebue",
    "pamc": "McGrath",
    "paom": "Nome",
    "patk": "Talkeetna",
    "paya": "Yakutat",
    "PAKV": "Kaltag",
    "PAEG": "Eagle",
    "PASC": "Deadhorse",
    "PAOR": "Northway",
    "PAGY": "Skagway",
    "PASI": "Sitka",
    "PAHO": "Homer",
}


def get_fdd_region_dropdown():
    return [{"label": label, "value": key} for key, label in FDD_REGION_OPTIONS.items()]


def get_fdd_station_dropdown():
    return [
        {"label": label, "value": sid}
        for sid, label in FDD_STATION_OPTIONS.items()
    ]


def get_current_water_year_dates():
    today = datetime.utcnow().date()
    year = today.year
    month = today.month

    # APRFC logic:
    # cold season starts Oct 1
    # after June, cap the season at June 1
    if month >= 10:
        sdate = f"{year}-10-01"
        edate = today.strftime("%Y-%m-%d")
    else:
        sdate = f"{year - 1}-10-01"
        if month > 5:
            edate = f"{year}-06-01"
        else:
            edate = today.strftime("%Y-%m-%d")

    return sdate, edate

def get_current_tdd_dates():
    today = datetime.utcnow().date()
    year = today.year

    sdate = f"{year}-01-01"
    edate = today.strftime("%Y-%m-%d")

    return sdate, edate


def fetch_acis_fdd_daily_series(station_id: str):
    sdate, edate = get_current_water_year_dates()

    params = {
        "sid": station_id,
        "sdate": sdate,
        "edate": edate,
        "elems": [
            {
                "name": "hdd32",
                "interval": "dly",
                "duration": "dly",
            }
        ],
    }

    try:
        r = requests.post(ACIS_STNDATA_URL, json=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"ACIS daily FDD request failed for {station_id}: {e}")
        return {
            "station_id": station_id,
            "station_name": FDD_STATION_OPTIONS.get(station_id, station_id),
            "data": [],
        }

    station_name = data.get("meta", {}).get(
        "name",
        FDD_STATION_OPTIONS.get(station_id, station_id),
    )

    rows = []
    cumulative = 0.0

    for row in data.get("data", []):
        if len(row) < 2:
            continue

        date = row[0]
        value = row[1]

        if value in ("M", "", None):
            daily_fdd = 0.0
        else:
            try:
                daily_fdd = float(value)
            except Exception:
                daily_fdd = 0.0

        cumulative += daily_fdd

        rows.append(
            {
                "date": date,
                "daily_fdd": daily_fdd,
                "cumulative_fdd": cumulative,
            }
        )

    return {
        "station_id": station_id,
        "station_name": station_name,
        "sdate": sdate,
        "edate": edate,
        "data": rows,
    }


def fetch_acis_fdd_total(station_id: str, sdate: str, edate: str):
    params = {
        "sid": station_id,
        "sdate": sdate,
        "edate": edate,
        "elems": [
            {
                "name": "hdd32",
                "interval": "dly",
                "duration": "dly",
            }
        ],
    }

    try:
        r = requests.post(ACIS_STNDATA_URL, json=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"ACIS FDD request failed for {station_id}: {e}")
        return None

    total = 0.0

    for row in data.get("data", []):
        if len(row) < 2:
            continue

        value = row[1]

        if value in ("M", "", None):
            continue

        try:
            total += float(value)
        except Exception:
            continue

    return total


def fetch_dynamic_fdd_percent_normal(station_id: str):
    sdate, edate = get_current_water_year_dates()
    current_fdd = fetch_acis_fdd_total(station_id, sdate, edate)

    if current_fdd is None:
        return None

    return {
        "current_fdd": current_fdd,
        "percent_normal": None,
        "label": f"{current_fdd:.0f}",
    }


def fetch_fdd_timeseries_placeholder(station_id: str):
    return {
        "station_id": station_id,
        "station_name": FDD_STATION_OPTIONS.get(station_id, station_id),
        "data": [
            {"date": "2026-01-01", "fdd": 10},
            {"date": "2026-01-02", "fdd": 22},
            {"date": "2026-01-03", "fdd": 35},
            {"date": "2026-01-04", "fdd": 48},
            {"date": "2026-01-05", "fdd": 60},
        ],
    }
    
    
ACIS_MULTISTNDATA_URL = "https://data.rcc-acis.org/MultiStnData"


def fetch_aprfc_fdd_map_geojson():
    sdate, edate = get_current_water_year_dates()

    sids = ",".join(FDD_STATION_OPTIONS.keys())

    data_params = {
        "sids": sids,
        "sdate": sdate,
        "edate": edate,
        "elems": [
            {
                "name": "hdd32",
                "interval": "dly",
                "duration": "dly",
            }
        ],
    }

    norm_params = {
        "sids": sids,
        "sdate": "2008-10-01",
        "edate": "2009-06-01",
        "elems": [
            {
                "name": "avgt",
                "interval": "dly",
                "duration": "dly",
                "normal": 1,
            }
        ],
    }

    try:
        data_res = requests.post(
            ACIS_MULTISTNDATA_URL,
            json=data_params,
            timeout=30,
        )
        data_res.raise_for_status()
        data_json = data_res.json()

        norm_res = requests.post(
            ACIS_MULTISTNDATA_URL,
            json=norm_params,
            timeout=30,
        )
        norm_res.raise_for_status()
        norm_json = norm_res.json()

    except Exception as e:
        print(f"APRFC FDD map request failed: {e}")
        return {
            "type": "FeatureCollection",
            "crs": {"properties": {"name": "EPSG:4326"}},
            "features": [],
        }

    norm_lookup = {
        item.get("meta", {}).get("name"): item
        for item in norm_json.get("data", [])
    }

    features = []

    for item in data_json.get("data", []):
        meta = item.get("meta", {})
        station_name = meta.get("name", "Unknown Station")
        ll = meta.get("ll")

        if not ll or len(ll) < 2:
            continue

        lon, lat = ll[0], ll[1]

        norm_item = norm_lookup.get(station_name)
        if not norm_item:
            continue

        total_fdd = 0.0
        total_norm = 0.0
        missing_count = 0

        data_rows = item.get("data", [])
        norm_rows = norm_item.get("data", [])

        for i, daily_row in enumerate(data_rows):
            if i >= len(norm_rows):
                break

            norm_row = norm_rows[i]

            # Extract data value
            if isinstance(daily_row, list):
                daily_value = daily_row[-1]
            else:
                daily_value = daily_row

            # Extract normal temperature value
            if isinstance(norm_row, list):
                norm_temp_value = norm_row[-1]
            else:
                norm_temp_value = norm_row

            try:
                normal_fdd = 32 - float(norm_temp_value)
                if normal_fdd < 0:
                    normal_fdd = 0
            except Exception:
                normal_fdd = 0

            total_norm += normal_fdd

            if daily_value in ("M", "", None):
                daily_fdd = normal_fdd
                missing_count += 1
            else:
                try:
                    daily_fdd = float(daily_value)
                except Exception:
                    daily_fdd = 0

            total_fdd += daily_fdd

        if total_norm == 0:
            total_norm = 1

        percent_normal = round((total_fdd / total_norm) * 100)

        if percent_normal > 200:
            percent_label = ">200%"
        else:
            percent_label = f"{percent_normal}%"

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "name": station_name,
                    "label": f"{round(total_fdd)}",
                    "fdd": round(total_fdd),
                    "percent_normal": percent_normal,
                    "percent_label": percent_label,
                    "missing_count": missing_count,
                    "sdate": sdate,
                    "edate": edate,
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "crs": {"properties": {"name": "EPSG:4326"}},
        "features": features,
    }
    
# ============================================================
# THAWING DEGREE DAYS CONFIG + HELPERS
# ============================================================

TDD_STATION_OPTIONS = FDD_STATION_OPTIONS
ACIS_MULTISTNDATA_URL = "https://data.rcc-acis.org/MultiStnData"


def get_tdd_station_dropdown():
    return [
        {"label": label, "value": sid}
        for sid, label in TDD_STATION_OPTIONS.items()
    ]


def fetch_acis_tdd_daily_series(station_id: str):
    sdate, edate = get_current_tdd_dates()

    params = {
        "sid": station_id,
        "sdate": sdate,
        "edate": edate,
        "elems": [
            {
                "name": "cdd32",
                "interval": "dly",
                "duration": "dly",
            }
        ],
    }

    try:
        r = requests.post(ACIS_STNDATA_URL, json=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"ACIS daily TDD request failed for {station_id}: {e}")
        return {
            "station_id": station_id,
            "station_name": TDD_STATION_OPTIONS.get(station_id, station_id),
            "data": [],
        }

    station_name = data.get("meta", {}).get(
        "name",
        TDD_STATION_OPTIONS.get(station_id, station_id),
    )

    rows = []
    cumulative = 0.0

    for row in data.get("data", []):
        if len(row) < 2:
            continue

        date = row[0]
        value = row[1]

        try:
            daily_tdd = 0.0 if value in ("M", "", None) else float(value)
        except Exception:
            daily_tdd = 0.0

        cumulative += daily_tdd

        rows.append({
            "date": date,
            "daily_tdd": daily_tdd,
            "cumulative_tdd": cumulative,
        })

    return {
        "station_id": station_id,
        "station_name": station_name,
        "sdate": sdate,
        "edate": edate,
        "data": rows,
    }
    
def fetch_aprfc_tdd_map_geojson():
    sdate, edate = get_current_tdd_dates()
    sids = ",".join(TDD_STATION_OPTIONS.keys())

    data_params = {
        "sids": sids,
        "sdate": sdate,
        "edate": edate,
        "elems": [
            {
                "name": "cdd32",
                "interval": "dly",
                "duration": "dly",
            }
        ],
    }

    norm_params = {
        "sids": sids,
        "sdate": "2008-10-01",
        "edate": "2009-06-01",
        "elems": [
            {
                "name": "avgt",
                "interval": "dly",
                "duration": "dly",
                "normal": 1,
            }
        ],
    }

    try:
        data_res = requests.post(ACIS_MULTISTNDATA_URL, json=data_params, timeout=30)
        data_res.raise_for_status()
        data_json = data_res.json()

        norm_res = requests.post(ACIS_MULTISTNDATA_URL, json=norm_params, timeout=30)
        norm_res.raise_for_status()
        norm_json = norm_res.json()

    except Exception as e:
        print(f"APRFC TDD map request failed: {e}")
        return {
            "type": "FeatureCollection",
            "crs": {"properties": {"name": "EPSG:4326"}},
            "features": [],
        }

    norm_lookup = {
        item.get("meta", {}).get("name"): item
        for item in norm_json.get("data", [])
    }

    features = []

    for item in data_json.get("data", []):
        meta = item.get("meta", {})
        station_name = meta.get("name", "Unknown Station")
        ll = meta.get("ll")

        if not ll or len(ll) < 2:
            continue

        lon, lat = ll[0], ll[1]

        norm_item = norm_lookup.get(station_name)
        if not norm_item:
            continue

        total_tdd = 0.0
        total_norm = 0.0
        missing_count = 0

        data_rows = item.get("data", [])
        norm_rows = norm_item.get("data", [])

        for i, daily_row in enumerate(data_rows):
            if i >= len(norm_rows):
                break

            norm_row = norm_rows[i]

            daily_value = daily_row[-1] if isinstance(daily_row, list) else daily_row
            norm_temp_value = norm_row[-1] if isinstance(norm_row, list) else norm_row

            try:
                normal_tdd = float(norm_temp_value) - 32
                if normal_tdd < 0:
                    normal_tdd = 0
            except Exception:
                normal_tdd = 0

            total_norm += normal_tdd

            if daily_value in ("M", "", None):
                daily_tdd = normal_tdd
                missing_count += 1
            else:
                try:
                    daily_tdd = float(daily_value)
                except Exception:
                    daily_tdd = 0

            total_tdd += daily_tdd

        if total_norm == 0:
            total_norm = 1

        percent_normal = round((total_tdd / total_norm) * 100)

        if percent_normal > 200:
            percent_label = ">200%"
        else:
            percent_label = f"{percent_normal}%"

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "name": station_name,
                    "label": f"{round(total_tdd)}",
                    "tdd": round(total_tdd),
                    "percent_normal": percent_normal,
                    "percent_label": percent_label,
                    "missing_count": missing_count,
                    "sdate": sdate,
                    "edate": edate,
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "crs": {"properties": {"name": "EPSG:4326"}},
        "features": features,
    }