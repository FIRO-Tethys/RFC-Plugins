# ============================================================
# APRFC SNOW DEPTH MAP PLUGIN
# ============================================================
# Product:
#   Water Supply -> Snow Depth
#
# Source page:
#   https://www.weather.gov/aprfc/Snow_Depth
#
# Data source:
#   https://www.weather.gov/source/aprfc/snow.json
#
# Purpose:
#   Show APRFC snow-depth stations on a TethysDash map.
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from intake.source import base


SNOW_JSON_URL = "https://www.weather.gov/source/aprfc/snow.json"


# ============================================================
# HELPERS
# ============================================================

def _fetch_json(url: str = SNOW_JSON_URL) -> Dict[str, Any]:
    """Fetch APRFC snow JSON."""
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def _parse_time(value: Any) -> Optional[datetime]:
    """Parse timestamp from APRFC snow data."""
    if value is None:
        return None

    try:
        if isinstance(value, (int, float)):
            if value > 10_000_000_000:
                value = value / 1000.0
            return datetime.fromtimestamp(value, tz=timezone.utc)

        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))

    except Exception:
        return None

    return None


def _clean_number(value: Any) -> Optional[float]:
    """Convert values to float safely."""
    if value in [None, "", "M"]:
        return None

    try:
        return float(value)
    except Exception:
        return None


def _format_number(value: Optional[float]) -> str:
    """Format numeric values for popup fields."""
    if value is None:
        return "Missing"

    try:
        return f"{float(value):g}"
    except Exception:
        return "Missing"


def _latest_pair(series: List[List[Any]]) -> tuple[Optional[Any], Optional[Any]]:
    """Return latest [time, value] pair."""
    if not series:
        return None, None

    latest = series[-1]

    if not isinstance(latest, list) or len(latest) < 2:
        return None, None

    return latest[0], latest[1]


def _snow_depth_category(value: Optional[float]) -> str:
    """Return snow-depth category string."""
    if value is None:
        return "Old or Missing"

    try:
        value = float(value)
    except Exception:
        return "Old or Missing"

    if value >= 60:
        return "60+ in"
    if value >= 49:
        return "49-60 in"
    if value >= 37:
        return "37-49 in"
    if value >= 25:
        return "25-37 in"
    if value >= 13:
        return "13-25 in"
    if value >= 7:
        return "7-13 in"
    if value >= 4:
        return "4-7 in"

    return "0-4 in"


def _build_snow_depth_geojson() -> Dict[str, Any]:
    """Build ArcGIS-safe GeoJSON from APRFC snow.json."""
    raw = _fetch_json()

    snow_depth_layer = raw.get("data", {}).get("sd", {})
    features = snow_depth_layer.get("features", []) or []

    features = snow_depth_layer.get("features", []) or []

    # TEMP TEST: only first 5 features
    features = features[:5]

    cleaned_features = []

    for idx, feature in enumerate(features, start=1):
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties", {}) or {}
        metadata = feature.get("metadata", {}) or {}

        # ArcGIS GeoJSONLayer is picky. Force clean 2D Point geometry.
        if geometry.get("type") != "Point":
            continue

        coords = geometry.get("coordinates")
        if not isinstance(coords, list) or len(coords) < 2:
            continue

        try:
            lon = float(coords[0])
            lat = float(coords[1])
        except Exception:
            continue

        # Skip invalid coordinates.
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            continue

        clean_geometry = {
            "type": "Point",
            "coordinates": [lon, lat],
        }

        lid = properties.get("lid")
        name = properties.get("name", lid)

        raw_data = properties.get("data", []) or []
        filtered_data = properties.get("filteredData", []) or []

        latest_filtered_time, latest_filtered_value = _latest_pair(filtered_data)
        latest_raw_time, latest_raw_value = _latest_pair(raw_data)

        snow_depth = _clean_number(latest_filtered_value)
        raw_snow_depth = _clean_number(latest_raw_value)

        latest_dt = _parse_time(latest_filtered_time)
        latest_time_text = (
            latest_dt.strftime("%Y-%m-%d %H:%M UTC")
            if latest_dt
            else "Missing"
        )

        category = _snow_depth_category(snow_depth)

        cleaned_features.append(
            {
                "type": "Feature",
                "id": idx,
                "geometry": clean_geometry,
                "properties": {
                    "ObjectID": idx,
                    "lid": str(lid) if lid is not None else "",
                    "name": str(name) if name is not None else "",
                    "category": str(category),
                    "snow_depth": _format_number(snow_depth),
                    "raw_snow_depth": _format_number(raw_snow_depth),
                    "latest_time": str(latest_time_text),
                    "unit": str(properties.get("dataunit", "in")),
                    "created": str(metadata.get("created", "")),
                },
            }
        )

    print(f"[APRFCSnowDepthViewer] features={len(cleaned_features)}")

    return {
        "type": "FeatureCollection",
        "features": cleaned_features,
    }


# ============================================================
# MAP PLUGIN
# ============================================================

class APRFCSnowDepthViewer(base.DataSource):
    """
    APRFC Snow Depth map viewer.
    """

    container = "python"
    version = "0.0.1"
    name = "aprfc_snow_depth_viewer"

    visualization_group = "Water Supply"
    visualization_label = "APRFC Snow Depth Map"
    visualization_type = "map"
    visualization_description = "Current APRFC snow-depth measurements in Alaska."
    visualization_tags = ["APRFC", "snow", "snow depth", "map", "water supply"]
    visualization_attribution = "NOAA/NWS APRFC; NRCS SNOTEL"

    visualization_args = {}

    loading_icon = False
    _user_parameters = []

    def __init__(self, metadata=None, **kwargs):
        super().__init__(metadata=metadata)

    def read(self):
        print("[APRFCSnowDepthViewer] read() called")

        snow_geojson = _build_snow_depth_geojson()

        return {
            "baseMap": (
                "https://server.arcgisonline.com/arcgis/rest/services/"
                "Canvas/World_Light_Gray_Base/MapServer"
            ),
            "layers": [
                {
                    "configuration": {
                        "type": "VectorLayer",
                        "props": {
                            "name": "APRFC Snow Depth",
                            "popup": {
                                "title": "{name}",
                                "content": (
                                    "<b>Station ID:</b> {lid}<br>"
                                    "<b>Snow Depth:</b> {snow_depth} in<br>"
                                    "<b>Raw Sensor Value:</b> {raw_snow_depth} in<br>"
                                    "<b>Category:</b> {category}<br>"
                                    "<b>Latest Time:</b> {latest_time}<br>"
                                    "<b>Unit:</b> {unit}"
                                ),
                            },

                            # Renderer removed for testing.
                            # If this loads, the renderer syntax was the issue.

                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": snow_geojson,
                            },
                        },
                    }
                }
            ],
            "layerControl": True,
            "map_extent": {
                "extent": "-16500000,8500000,3.8"
            },
        }