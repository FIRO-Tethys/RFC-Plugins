# ============================================================
# APRFC NRCS SWE TIME-SERIES PLUGIN
# ============================================================
# Product:
#   Water Supply -> NRCS SWE Data
#
# Source page:
#   https://www.weather.gov/aprfc/nrcs_AK_SWE
#
# Data source:
#   https://www.weather.gov/source/aprfc/nrcs_swe.json
#
# Purpose:
#   Show 30-day SWE and average SWE time series for selected
#   NRCS/SNOTEL station.
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from intake.source import base


NRCS_SWE_JSON_URL = "https://www.weather.gov/source/aprfc/nrcs_swe.json"


# ============================================================
# HTTP / DATA HELPERS
# ============================================================

def _fetch_json(url: str = NRCS_SWE_JSON_URL) -> Dict[str, Any]:
    """Fetch APRFC NRCS SWE GeoJSON."""
    with httpx.Client(timeout=40.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def _get_swe_features() -> List[Dict[str, Any]]:
    """Return features from APRFC NRCS SWE GeoJSON."""
    raw = _fetch_json()
    return raw.get("features", []) or []


def _clean_number(value: Any) -> Optional[float]:
    """Convert values to float safely."""
    if value in [None, "", "M", "T"]:
        if value == "T":
            return 0.0
        return None

    try:
        return float(value)
    except Exception:
        return None


def _parse_time(value: Any) -> Optional[datetime]:
    """Parse APRFC/JavaScript timestamps safely."""
    if value is None:
        return None

    try:
        if isinstance(value, (int, float)):
            # JavaScript timestamps are usually milliseconds.
            if value > 10_000_000_000:
                value = value / 1000.0
            return datetime.fromtimestamp(value, tz=timezone.utc)

        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))

    except Exception:
        return None

    return None


def _series_to_plotly(series: List[List[Any]]) -> Tuple[List[str], List[Optional[float]]]:
    """Convert [time, value] series to Plotly x/y arrays."""
    x_values = []
    y_values = []

    for item in series:
        if not isinstance(item, list) or len(item) < 2:
            continue

        dt = _parse_time(item[0])
        val = _clean_number(item[1])

        if dt is None:
            continue

        x_values.append(dt.isoformat())
        y_values.append(val)

    return x_values, y_values


def _normalize_station_value(value: Any) -> str:
    """
    Normalize dropdown/map-click value.

    Examples:
        ABCD
        ABCD - Station Name
    """
    if value is None:
        return ""

    value = str(value).strip()

    if " - " in value:
        return value.split(" - ", 1)[0].strip()

    if "|" in value:
        return value.split("|", 1)[0].strip()

    return value


def _get_station_choices_for_dropdown() -> List[str]:
    """
    Build station dropdown from nrcs_swe.json.

    TethysDash dropdown values are simple strings, so use LID only.
    """
    try:
        features = _get_swe_features()
        lids = []

        for feature in features:
            props = feature.get("properties", {}) or {}
            lid = props.get("lid")
            if lid:
                lids.append(str(lid).upper())

        lids = sorted(set(lids))
        return lids or [""]

    except Exception:
        return [""]


def _find_station(swe_lid: str) -> Optional[Dict[str, Any]]:
    """Find station feature by LID."""
    swe_lid_clean = _normalize_station_value(swe_lid).upper()

    for feature in _get_swe_features():
        props = feature.get("properties", {}) or {}
        lid = str(props.get("lid", "")).upper()

        if lid == swe_lid_clean:
            return feature

    return None


# ============================================================
# DROPDOWN CHOICES
# ============================================================

SWE_STATION_CHOICES = _get_station_choices_for_dropdown()


# ============================================================
# TIME-SERIES PLUGIN
# ============================================================

class APRFCNRCSSWETimeSeries(base.DataSource):
    """
    APRFC NRCS SWE 30-day time-series viewer.

    This is the time-series companion to the NRCS SWE map plugin.
    """

    container = "python"
    version = "0.0.1"
    name = "aprfc_nrcs_swe_time_series"

    visualization_group = "Water Supply"
    visualization_label = "APRFC NRCS SWE Time Series"
    visualization_type = "plotly"
    visualization_description = (
        "30-day NRCS/SNOTEL SWE and average SWE time series for selected Alaska station."
    )
    visualization_tags = ["aprfc", "nrcs", "swe", "snow", "time series", "water supply"]
    visualization_attribution = "NOAA/NWS APRFC; NRCS SNOTEL"

    visualization_args = {
        "swe_lid": SWE_STATION_CHOICES,
    }

    loading_icon = True
    _user_parameters: List[Any] = []

    def __init__(self, swe_lid: str = "", metadata=None, **kwargs):
        super().__init__(metadata=metadata)

        if not swe_lid and SWE_STATION_CHOICES:
            swe_lid = SWE_STATION_CHOICES[0]

        self.swe_lid = _normalize_station_value(swe_lid)

    def read(self):
        feature = _find_station(self.swe_lid)

        if feature is None:
            return {
                "data": [],
                "layout": {
                    "title": f"No NRCS SWE data found for station: {self.swe_lid}",
                    "xaxis": {"title": "Time"},
                    "yaxis": {"title": "SWE (in)"},
                },
            }

        props = feature.get("properties", {}) or {}

        lid = props.get("lid", self.swe_lid)
        station_name = props.get("name", lid)
        data_name = props.get("dataname", "SWE")
        data_unit = props.get("dataunit", "in")

        swe_data = props.get("data", []) or []
        avg_data = props.get("avg", []) or []

        swe_x, swe_y = _series_to_plotly(swe_data)
        avg_x, avg_y = _series_to_plotly(avg_data)

        traces = [
            {
                "type": "scatter",
                "mode": "lines",
                "name": data_name,
                "x": swe_x,
                "y": swe_y,
                "line": {
                    "color": "#0000cc",
                    "width": 2,
                },
                "hovertemplate": (
                    "<b>SWE</b><br>"
                    "%{x}: %{y:.2f} in"
                    "<extra></extra>"
                ),
            }
        ]

        if avg_x and avg_y:
            traces.append(
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Average SWE",
                    "x": avg_x,
                    "y": avg_y,
                    "line": {
                        "color": "black",
                        "width": 2,
                        "dash": "dash",
                    },
                    "hovertemplate": (
                        "<b>Average SWE</b><br>"
                        "%{x}: %{y:.2f} in"
                        "<extra></extra>"
                    ),
                }
            )

        return {
            "data": traces,
            "layout": {
                "title": {
                    "text": f"{station_name} ({lid})<br><sup>{data_name} - Last 30 Days</sup>",
                    "x": 0.5,
                    "xanchor": "center",
                },
                "xaxis": {
                    "title": "Date",
                    "type": "date",
                },
                "yaxis": {
                    "title": data_unit,
                    "rangemode": "tozero",
                },
                "hovermode": "x unified",
                "legend": {
                    "orientation": "h",
                    "x": 0.5,
                    "xanchor": "center",
                    "y": -0.2,
                },
                "margin": {
                    "l": 70,
                    "r": 40,
                    "t": 90,
                    "b": 90,
                },
                "height": 450,
            },
        }