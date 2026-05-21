# ============================================================
# APRFC SNOW DEPTH TIME-SERIES PLUGIN
# ============================================================
# Product:
#   Water Supply -> Snow Depth
#
# Current data source:
#   https://www.weather.gov/source/aprfc/snow.json
#
# Historical/archive data source:
#   https://data.rcc-acis.org/StnMeta
#   https://data.rcc-acis.org/StnData
#
# Purpose:
#   1. Dropdown of current snow-depth stations from snow.json
#   2. Top plot: 30-day raw/smoothed snow depth from snow.json
#   3. Bottom plot: annual historical snow-depth curves from RCC-ACIS/xmACIS
# ============================================================

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

import httpx
from intake.source import base


SNOW_JSON_URL = "https://www.weather.gov/source/aprfc/snow.json"
LID_TO_ACIS_LOOKUP_JS_URL = "https://www.weather.gov/source/aprfc/js/nwsLID2xmAcis_lookupJson.js"

ACIS_STNMETA_URL = "https://data.rcc-acis.org/StnMeta"
ACIS_STNDATA_URL = "https://data.rcc-acis.org/StnData"


# ============================================================
# HTTP HELPERS
# ============================================================

def _fetch_json(url: str) -> Dict[str, Any]:
    """Fetch JSON from a URL."""
    with httpx.Client(timeout=40.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def _fetch_text(url: str) -> str:
    """Fetch plain text from a URL."""
    with httpx.Client(timeout=40.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def _post_form_json(url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """POST form data and return JSON."""
    with httpx.Client(timeout=70.0, follow_redirects=True) as client:
        response = client.post(url, data=data)
        response.raise_for_status()
        return response.json()


# ============================================================
# TIME / VALUE HELPERS
# ============================================================

def _parse_time(value: Any) -> Optional[datetime]:
    """Parse APRFC timestamp safely."""
    if value is None:
        return None

    try:
        if isinstance(value, (int, float)):
            # JS timestamps are usually milliseconds.
            if value > 10_000_000_000:
                value = value / 1000.0
            return datetime.fromtimestamp(value, tz=timezone.utc)

        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))

    except Exception:
        return None

    return None


def _parse_acis_date(value: Any) -> Optional[datetime]:
    """Parse ACIS daily date string."""
    try:
        return datetime.fromisoformat(str(value)).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _clean_number(value: Any) -> Optional[float]:
    """Convert snow values to float safely."""
    if value in [None, "", "M"]:
        return None

    if value == "T":
        return 0.0

    try:
        return float(value)
    except Exception:
        return None


def _series_to_plotly(series: List[List[Any]]) -> Tuple[List[str], List[Optional[float]]]:
    """Convert APRFC [time, value] list to Plotly x/y arrays."""
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


# ============================================================
# CURRENT SNOW.JSON HELPERS
# ============================================================

def _get_snow_features() -> List[Dict[str, Any]]:
    """Return current snow-depth features from APRFC snow.json."""
    raw = _fetch_json(SNOW_JSON_URL)
    return raw.get("data", {}).get("sd", {}).get("features", []) or []


def _normalize_station_value(value: Any) -> str:
    """
    Normalize dropdown/map-click value.

    Examples:
        FYNA2
        FYNA2 - Fort Yukon Snotel
    """
    if value is None:
        return "PAYA2"

    value = str(value).strip()

    if " - " in value:
        return value.split(" - ", 1)[0].strip()

    if "|" in value:
        return value.split("|", 1)[0].strip()

    return value


def _find_station(snow_lid: str) -> Optional[Dict[str, Any]]:
    """Find one current snow-depth station from APRFC snow.json by LID."""
    snow_lid_clean = _normalize_station_value(snow_lid)

    for feature in _get_snow_features():
        props = feature.get("properties", {})
        lid = props.get("lid")

        if str(lid).upper() == str(snow_lid_clean).upper():
            return feature

    return None


def _get_station_choices_for_dropdown() -> List[str]:
    """
    Build dropdown choices from snow.json.

    TethysDash dropdown values are simple strings, so use LID only.
    """
    try:
        features = _get_snow_features()
        lids = []

        for feature in features:
            props = feature.get("properties", {})
            lid = props.get("lid")
            if lid:
                lids.append(str(lid).upper())

        lids = sorted(set(lids))
        return lids or ["PAYA2"]

    except Exception:
        return ["PAYA2"]


# ============================================================
# LID -> ACIS LOOKUP HELPERS
# ============================================================

def _get_lid_to_acis_lookup() -> Dict[str, str]:
    """
    Fetch and parse APRFC's NWS LID -> xmACIS lookup JavaScript.

    The file looks like:
        var lookup = {
            "FYNA2": "US0045R01S 6",
            ...
        }
    """
    try:
        text = _fetch_text(LID_TO_ACIS_LOOKUP_JS_URL)

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            print("Could not find JSON object in APRFC LID-to-ACIS lookup JS.")
            print(text[:500])
            return {}

        lookup_text = text[start:end + 1]
        lookup_text = re.sub(r"//.*", "", lookup_text)
        lookup_text = lookup_text.replace("'", '"')

        lookup = json.loads(lookup_text)

        return {
            str(k).strip().upper(): str(v).strip()
            for k, v in lookup.items()
            if k and v
        }

    except Exception as exc:
        print(f"Failed to load/parse LID-to-ACIS lookup: {exc}")
        return {}


# ============================================================
# ACIS STATION FALLBACK HELPERS
# ============================================================

def _normalize_name_for_match(value: str) -> str:
    """Normalize station names for loose matching."""
    if value is None:
        return ""

    value = str(value).lower()
    value = value.replace("snotel", "")
    value = value.replace("sntl", "")
    value = value.replace("coop", "")
    value = value.replace("co-op", "")
    value = value.replace("snow", "")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _find_acis_sid_by_station_name(station_name: str) -> Optional[str]:
    """
    Fallback: search RCC-ACIS station metadata by station name.

    Prefer active/current snow-depth stations and SNOTEL/SNTL matches.
    """
    try:
        target = _normalize_name_for_match(station_name)
        target_raw = str(station_name).lower()

        params = {
            "bbox": "-180,50,-120,75",
            "meta": "name,sids,ll,valid_daterange",
            "elems": "snwd",
            "sdate": "1800-1-1",
            "edate": "2100-1-1",
        }

        response = _post_form_json(ACIS_STNMETA_URL, params)
        stations = response.get("meta", []) or []

        best_sid = None
        best_score = -999999
        best_name = None
        best_range = None

        for station in stations:
            acis_name = station.get("name", "")
            acis_name_raw = str(acis_name).lower()
            acis_norm = _normalize_name_for_match(acis_name)

            if not acis_norm:
                continue

            valid_range = station.get("valid_daterange", [[]])
            if not valid_range or not valid_range[0] or len(valid_range[0]) < 2:
                continue

            start_date = str(valid_range[0][0])
            end_date = str(valid_range[0][1])

            sids = station.get("sids", [])
            if not sids:
                continue

            score = 0

            if acis_norm == target:
                score += 100
            elif target in acis_norm or acis_norm in target:
                score += 80
            else:
                target_words = set(target.split())
                acis_words = set(acis_norm.split())
                shared = target_words.intersection(acis_words)
                score += len(shared) * 10

            try:
                end_year = int(end_date[:4])
                if end_year >= 2020:
                    score += 100
                elif end_year < 2000:
                    score -= 100
            except Exception:
                pass

            if "snotel" in target_raw or "sntl" in target_raw:
                if "snotel" in acis_name_raw or "sntl" in acis_name_raw:
                    score += 80
                else:
                    score -= 30

            if ("snotel" in target_raw or "sntl" in target_raw) and "coop" in acis_name_raw:
                score -= 60

            if score > best_score:
                best_sid = sids[0]
                best_score = score
                best_name = acis_name
                best_range = (start_date, end_date)

        if best_sid:
            print(
                f"ACIS fallback matched '{station_name}' -> "
                f"'{best_name}' -> {best_sid}, POR={best_range}, score={best_score}"
            )
            return best_sid

        print(f"ACIS fallback found no station-name match for '{station_name}'")
        return None

    except Exception as exc:
        print(f"ACIS fallback station-name search failed: {exc}")
        return None


def _get_acis_sid_for_lid(snow_lid: str, station_name: Optional[str] = None) -> Optional[str]:
    """
    Return xmACIS/RCC-ACIS station ID for APRFC/NWS LID.

    First uses APRFC lookup JS.
    If that fails, falls back to RCC-ACIS station-name search.
    """
    lookup = _get_lid_to_acis_lookup()
    sid = lookup.get(str(snow_lid).upper())

    if sid:
        return sid

    if station_name:
        return _find_acis_sid_by_station_name(station_name)

    return None


# ============================================================
# ACIS HISTORICAL DATA HELPERS
# ============================================================

def _get_acis_meta(acis_sid: str) -> Optional[Dict[str, Any]]:
    """Fetch ACIS station metadata for snow depth."""
    try:
        params = {
            "sids": acis_sid,
            "meta": "name,sids,ll,valid_daterange",
            "elems": "snwd",
            "sdate": "1800-1-1",
            "edate": "2100-1-1",
        }

        response = _post_form_json(ACIS_STNMETA_URL, params)
        meta = response.get("meta", [])

        if not meta:
            return None

        return meta[0]

    except Exception as exc:
        print(f"Failed to fetch ACIS metadata for {acis_sid}: {exc}")
        return None


def _get_acis_snow_data(acis_sid: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    """Fetch daily historical snow-depth data from ACIS."""
    try:
        params = {
            "sid": acis_sid,
            "sDate": start_date,
            "eDate": end_date,
            "elems": [{"name": "snwd"}],
        }

        response = _post_form_json(
            ACIS_STNDATA_URL,
            {
                "params": json.dumps(params),
                "output": "json",
            },
        )

        return response

    except Exception as exc:
        print(f"Failed to fetch ACIS snow data for {acis_sid}: {exc}")
        return None


def _water_year(dt: datetime) -> int:
    """Sep-Dec belong to next year; Jan-Aug belong to current year."""
    if dt.month >= 9:
        return dt.year + 1
    return dt.year


def _dummy_snow_year_date(dt: datetime) -> datetime:
    """
    Shift dates to common display snow-season year.

    Sep-Dec -> 2000
    Jan-Aug -> 2001
    """
    display_year = 2000 if dt.month >= 9 else 2001

    try:
        return datetime(display_year, dt.month, dt.day, tzinfo=timezone.utc)
    except ValueError:
        return datetime(display_year, dt.month, 28, tzinfo=timezone.utc)


def _build_historical_traces(
    acis_data: Dict[str, Any],
    current_filtered_data: Optional[List[List[Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Build Plotly traces for annual historical snow-depth chart.

    APRFC-like colors:
      - light gray = historic years
      - tan/brown = max year
      - black = average/median
      - red = current year
      - red = realtime 30 days
    """
    rows = acis_data.get("data", []) or []

    by_year: Dict[int, List[Tuple[datetime, float]]] = defaultdict(list)
    values_by_day_index: Dict[int, List[float]] = defaultdict(list)

    season_start = datetime(2000, 9, 1, tzinfo=timezone.utc)

    for row in rows:
        if not isinstance(row, list) or len(row) < 2:
            continue

        dt = _parse_acis_date(row[0])
        value = _clean_number(row[1])

        if dt is None or value is None:
            continue

        wy = _water_year(dt)
        shifted_dt = _dummy_snow_year_date(dt)
        day_index = (shifted_dt - season_start).days

        by_year[wy].append((shifted_dt, value))
        values_by_day_index[day_index].append(value)

    traces: List[Dict[str, Any]] = []
    current_wy = _water_year(datetime.now(timezone.utc))

    max_wy = None
    max_peak = -1.0

    for wy, points in by_year.items():
        if not points:
            continue

        peak = max(value for _, value in points)

        if peak > max_peak:
            max_peak = peak
            max_wy = wy

    for wy in sorted(by_year.keys()):
        points = sorted(by_year[wy], key=lambda item: item[0])

        if len(points) < 10:
            continue

        x = [p[0].isoformat() for p in points]
        y = [p[1] for p in points]

        season_label = f"{wy - 1}-{wy}"

        peak_value = max(y)
        peak_index = y.index(peak_value)
        peak_date = points[peak_index][0].strftime("%b %d")
        avg_value = sum(y) / len(y) if y else 0

        customdata = [
            [season_label, peak_value, peak_date, avg_value]
            for _ in x
        ]

        is_current = wy == current_wy
        is_max = wy == max_wy

        if is_current:
            trace_name = season_label
            line_color = "red"
            line_width = 2.5
            showlegend = True
        elif is_max:
            trace_name = f"Max {season_label}"
            line_color = "#c49a6c"
            line_width = 2.5
            showlegend = True
        else:
            trace_name = season_label
            line_color = "rgba(190,190,190,0.35)"
            line_width = 1
            showlegend = False

        traces.append(
            {
                "type": "scatter",
                "mode": "lines",
                "name": trace_name,
                "x": x,
                "y": y,
                "xaxis": "x2",
                "yaxis": "y2",
                "legend": "legend2",
                "customdata": customdata,
                "line": {
                    "width": line_width,
                    "color": line_color,
                },
                "showlegend": showlegend,
                "hovertemplate": (
                    "<b>%{customdata[0]}</b><br>"
                    "%{x|%b %d}: %{y:.1f} in<br>"
                    "Season max: %{customdata[1]:.1f} in on %{customdata[2]}<br>"
                    "Season average: %{customdata[3]:.1f} in"
                    "<extra></extra>"
                ),
            }
        )

    # Median line.
    median_x = []
    median_y = []

    for day_index in sorted(values_by_day_index.keys()):
        vals = values_by_day_index[day_index]
        if not vals:
            continue

        shifted = season_start + timedelta(days=day_index)
        median_x.append(shifted.isoformat())
        median_y.append(median(vals))

    if median_x:
        traces.append(
            {
                "type": "scatter",
                "mode": "lines",
                "name": "Average / Median",
                "x": median_x,
                "y": median_y,
                "xaxis": "x2",
                "yaxis": "y2",
                "legend": "legend2",
                "line": {
                    "width": 3,
                    "color": "black",
                },
                "showlegend": True,
                "hovertemplate": (
                    "<b>Average / Median</b><br>"
                    "%{x|%b %d}: %{y:.1f} in"
                    "<extra></extra>"
                ),
            }
        )

    # Current 30-day filtered data shifted onto annual plot.
    if current_filtered_data:
        current_x = []
        current_y = []

        for item in current_filtered_data:
            if not isinstance(item, list) or len(item) < 2:
                continue

            dt = _parse_time(item[0])
            val = _clean_number(item[1])

            if dt is None or val is None:
                continue

            shifted = _dummy_snow_year_date(dt)
            current_x.append(shifted.isoformat())
            current_y.append(val)

        if current_x:
            traces.append(
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": "RealTime Data - 30 days",
                    "x": current_x,
                    "y": current_y,
                    "xaxis": "x2",
                    "yaxis": "y2",
                    "legend": "legend2",
                    "line": {
                        "width": 3,
                        "color": "red",
                    },
                    "showlegend": True,
                    "hovertemplate": (
                        "<b>RealTime Data - 30 days</b><br>"
                        "%{x|%b %d}: %{y:.1f} in"
                        "<extra></extra>"
                    ),
                }
            )

    return traces


def _build_historical_plot_for_lid(
    snow_lid: str,
    station_name: Optional[str] = None,
    current_filtered_data: Optional[List[List[Any]]] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Build historical annual traces for a snow station."""
    acis_sid = _get_acis_sid_for_lid(snow_lid, station_name=station_name)

    if not acis_sid:
        return [], f"No xmACIS/RCC-ACIS mapping found for {snow_lid}."

    meta = _get_acis_meta(acis_sid)

    if not meta:
        return [], f"No ACIS metadata found for {snow_lid} / {acis_sid}."

    valid_range = meta.get("valid_daterange", [[]])

    if not valid_range or not valid_range[0] or len(valid_range[0]) < 2:
        return [], f"No ACIS valid date range found for {snow_lid} / {acis_sid}."

    start_date = valid_range[0][0]
    end_date = valid_range[0][1]

    acis_data = _get_acis_snow_data(acis_sid, start_date, end_date)

    if not acis_data:
        return [], f"No ACIS snow-depth data found for {snow_lid} / {acis_sid}."

    traces = _build_historical_traces(
        acis_data,
        current_filtered_data=current_filtered_data,
    )

    station_name_from_meta = meta.get("name", station_name or snow_lid)
    subtitle = (
        f"{station_name_from_meta} historical snow depth, "
        f"period of record: {start_date} to {end_date}"
    )

    return traces, subtitle


# ============================================================
# DROPDOWN CHOICES
# ============================================================

SNOW_STATION_CHOICES = _get_station_choices_for_dropdown()


# ============================================================
# TIME-SERIES PLUGIN
# ============================================================

class APRFCSnowDepthTimeSeries(base.DataSource):
    """
    APRFC Snow Depth time-series viewer.
    """

    container = "rfc_plugins"
    version = "0.0.1"
    name = "aprfc_snow_depth_time_series"

    visualization_group = "Water Supply"
    visualization_label = "APRFC Snow Depth Time Series"
    visualization_type = "plotly"
    visualization_description = (
        "30-day current snow-depth time series and historical annual snow-depth "
        "comparison for selected APRFC station."
    )
    visualization_tags = ["APRFC", "snow", "snow depth", "time series", "water supply"]
    visualization_attribution = "NOAA/NWS APRFC; NRCS SNOTEL; RCC-ACIS/xmACIS"

    visualization_args = {
        "snow_lid": SNOW_STATION_CHOICES,
    }

    loading_icon = True

    _user_parameters: List[Any] = []

    def __init__(self, snow_lid: str = "PAYA2", metadata=None):
        super().__init__(metadata=metadata)
        self.snow_lid = _normalize_station_value(snow_lid)

    def read(self):
        feature = _find_station(self.snow_lid)

        if feature is None:
            return {
                "data": [],
                "layout": {
                    "title": f"No snow-depth data found for station: {self.snow_lid}",
                    "xaxis": {"title": "Time"},
                    "yaxis": {"title": "Snow Depth (in)"},
                },
            }

        props = feature.get("properties", {})

        station_name = props.get("name", self.snow_lid)
        unit = props.get("dataunit", "in")
        data_name = props.get("dataname", "Snow Depth")

        raw_data = props.get("data", []) or []
        filtered_data = props.get("filteredData", []) or []

        raw_x, raw_y = _series_to_plotly(raw_data)
        filtered_x, filtered_y = _series_to_plotly(filtered_data)

        plot_data: List[Dict[str, Any]] = [
            {
                "type": "scatter",
                "mode": "lines",
                "name": f"{data_name} (Raw Sensor Values)",
                "x": raw_x,
                "y": raw_y,
                "xaxis": "x",
                "yaxis": "y",
                "legend": "legend",
                "line": {
                    "color": "#00aaff",
                    "width": 2,
                },
                "showlegend": True,
                "hovertemplate": (
                    "<b>Raw Sensor Values</b><br>"
                    "%{x}: %{y:.1f} in"
                    "<extra></extra>"
                ),
            },
            {
                "type": "scatter",
                "mode": "lines",
                "name": f"{data_name} (Smoothed Values)",
                "x": filtered_x,
                "y": filtered_y,
                "xaxis": "x",
                "yaxis": "y",
                "legend": "legend",
                "line": {
                    "color": "#0000cc",
                    "width": 2,
                },
                "showlegend": True,
                "hovertemplate": (
                    "<b>Smoothed Values</b><br>"
                    "%{x}: %{y:.1f} in"
                    "<extra></extra>"
                ),
            },
        ]

        historical_traces, historical_note = _build_historical_plot_for_lid(
            self.snow_lid,
            station_name=station_name,
            current_filtered_data=filtered_data,
        )

        plot_data.extend(historical_traces)

        if historical_traces:
            bottom_title = "Annual Historical Snow Depth Plot"
            bottom_subtitle = historical_note or ""
        else:
            bottom_title = f"Annual Historical Snow Depth unavailable: {historical_note}"
            bottom_subtitle = ""

        return {
            "data": plot_data,
            "layout": {
                "title": {
                    "text": (
                        f"{station_name} ({self.snow_lid}) Snow Depth<br>"
                        f"<sup>Top: 30-day current data from APRFC snow.json. "
                        f"Bottom: historical daily snow depth from RCC-ACIS when available.</sup>"
                    ),
                    "x": 0.5,
                    "xanchor": "center",
                },

                # ====================================================
                # TOP PANEL
                # ====================================================
                "xaxis": {
                    "title": "Current Time",
                    "type": "date",
                    "domain": [0.0, 0.82],
                    "anchor": "y",
                },
                "yaxis": {
                    "title": f"30-Day Snow Depth ({unit})",
                    "domain": [0.67, 0.96],
                    "rangemode": "tozero",
                    "anchor": "x",
                },

                # ====================================================
                # BOTTOM PANEL
                # ====================================================
                "xaxis2": {
                    "title": "Snow Season",
                    "type": "date",
                    "domain": [0.0, 0.82],
                    "anchor": "y2",
                    "tickformat": "%b %d",
                    "range": [
                        datetime(2000, 9, 1, tzinfo=timezone.utc).isoformat(),
                        datetime(2001, 9, 1, tzinfo=timezone.utc).isoformat(),
                    ],
                },
                "yaxis2": {
                    "title": "Annual Snow Depth (in)",
                    "domain": [0.06, 0.43],
                    "rangemode": "tozero",
                    "anchor": "x2",
                },

                "annotations": [
                    {
                        "text": "30-Day Snow Depth Plot",
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.41,
                        "y": 1.01,
                        "showarrow": False,
                        "font": {"size": 16},
                    },
                    {
                        "text": bottom_title,
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.41,
                        "y": 0.49,
                        "showarrow": False,
                        "font": {"size": 16},
                    },
                    {
                        "text": bottom_subtitle,
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.41,
                        "y": 0.455,
                        "showarrow": False,
                        "font": {"size": 11},
                    },
                ],

                "hovermode": "closest",

                # Top legend: under upper plot, like APRFC.
                "legend": {
                    "orientation": "h",
                    "x": 0.41,
                    "xanchor": "center",
                    "y": 0.615,
                    "yanchor": "top",
                    "font": {"size": 12},
                },

                # Bottom legend: right of lower plot, like APRFC.
                "legend2": {
                    "orientation": "v",
                    "x": 0.86,
                    "xanchor": "left",
                    "y": 0.43,
                    "yanchor": "top",
                    "font": {"size": 12},
                    "title": {
                        "text": "<i>Hover to Highlight Years</i>"
                    },
                },

                "margin": {
                    "l": 80,
                    "r": 240,
                    "t": 130,
                    "b": 90,
                },

                "height": 1000,
            },
        }