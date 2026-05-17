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