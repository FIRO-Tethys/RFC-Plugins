from intake.source import base
from datetime import datetime, timedelta
import requests


ACIS_STNDATA_URL = "https://data.rcc-acis.org/StnData"

STATION_OPTIONS = {
    "PAFA": "Fairbanks",
    "PANC": "Anchorage",
    "PAEN": "Kenai",
    "PABR": "Utqiagvik / Barrow",
    "PABE": "Bethel",
    "PAOM": "Nome",
    "PAOT": "Kotzebue",
    "PAMC": "McGrath",
    "PAHO": "Homer",
    "PAJN": "Juneau",
}

SHOW_FREEZING_LINE = True

def get_station_dropdown():
    return [{"label": label, "value": sid} for sid, label in STATION_OPTIONS.items()]


def clean_value(v):
    try:
        return None if v in ("M", "", None) else float(v)
    except Exception:
        return None
    
def fetch_nbm_temperature_ranges(site_id, forecast="1"):
    url = "https://data.chenabasin.org/getNBM.php"

    params = {
        "site": site_id,
        "forecast": forecast,
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        result = r.json()
    except Exception as e:
        print(f"NBM request failed for {site_id}: {e}")
        return [], [], [], None

    dates = []
    lows = []
    highs = []

    point_low = None

    for item in result.get("data", []):
        validtime = item.get("validtime")
        txn = clean_value(item.get("TXN"))

        if not validtime or txn is None:
            continue

        dt = datetime.fromisoformat(validtime.replace("Z", "+00:00"))

        if dt.hour == 0 and point_low is not None:
            forecast_date = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
            dates.append(forecast_date)
            lows.append(point_low)
            highs.append(txn)
            point_low = None
        else:
            point_low = txn

    return dates, lows, highs, result.get("basistime")

def fetch_nws_forecast_temperature_ranges(lat, lon):
    headers = {
        "User-Agent": "RFC TethysDash Plugin (iman.maghami@example.com)"
    }

    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        r = requests.get(points_url, headers=headers, timeout=30)
        r.raise_for_status()
        forecast_url = r.json()["properties"]["forecast"]

        r = requests.get(forecast_url, headers=headers, timeout=30)
        r.raise_for_status()
        periods = r.json()["properties"]["periods"]

    except Exception as e:
        print(f"NWS forecast request failed: {e}")
        return [], [], []

    daily = {}

    for p in periods:
        temp = p.get("temperature")
        start_time = p.get("startTime")
        is_daytime = p.get("isDaytime")

        if temp is None or not start_time:
            continue

        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        date_str = (dt + timedelta(hours=6)).strftime("%Y-%m-%d")

        daily.setdefault(date_str, {"low": None, "high": None})

        if is_daytime:
            daily[date_str]["high"] = temp
        else:
            daily[date_str]["low"] = temp

    dates, lows, highs = [], [], []

    for d, vals in daily.items():
        if vals["low"] is not None and vals["high"] is not None:
            dates.append(d)
            lows.append(vals["low"])
            highs.append(vals["high"])

    print("NWS forecast count:", len(dates))

    return dates, lows, highs


class APRFCBreakupTemperatureOutlooksViewer(base.DataSource):
    container = "python"
    version = "0.0.2"
    name = "aprfc_breakup_temperature_outlooks"

    visualization_group = "Seasonal Interest"
    visualization_label = "Breakup Temperature Outlooks"
    visualization_type = "plotly"
    visualization_description = "Observed air temperatures, normals, and records for spring breakup monitoring."
    visualization_tags = ["aprfc", "seasonal", "breakup", "temperature", "acis", "plotly"]
    visualization_attribution = "RCC-ACIS / NOAA"

    visualization_args = {
        "station_id": get_station_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, station_id="PAFA", metadata=None, **kwargs):
        self.station_id = station_id
        super().__init__(metadata=metadata)

    def _fetch_acis_daily(self):
        params = {
            "sid": self.station_id,
            "sdate": "2026-03-01",
            "edate": "2026-06-01",
            "meta": ["name", "state", "valid_daterange", "sids", "ll"],
            "elems": [
                {"name": "maxt", "interval": "dly", "duration": "dly"},
                {"name": "mint", "interval": "dly", "duration": "dly"},
                {"name": "maxt", "interval": "dly", "duration": "dly", "normal": 1},
                {"name": "mint", "interval": "dly", "duration": "dly", "normal": 1},
            ],
        }

        r = requests.post(ACIS_STNDATA_URL, json=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def _fetch_acis_records(self):
        params = {
            "sid": self.station_id,
            "sdate": "1840-03-01",
            "edate": "2030-06-01",
            "meta": ["name", "state", "valid_daterange", "sids"],
            "elems": [
                {
                    "name": "maxt",
                    "interval": "dly",
                    "duration": "dly",
                    "smry": {"reduce": "max", "add": "date"},
                    "smry_only": 1,
                    "groupby": ["year", "03-01", "06-01"],
                },
                {
                    "name": "mint",
                    "interval": "dly",
                    "duration": "dly",
                    "smry": {"reduce": "min", "add": "date"},
                    "smry_only": 1,
                    "groupby": ["year", "03-01", "06-01"],
                },
            ],
        }

        r = requests.post(ACIS_STNDATA_URL, json=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def read(self):
        try:
            data = self._fetch_acis_daily()
            records = self._fetch_acis_records()
        except Exception as e:
            return {
                "data": [],
                "layout": {"title": f"Could not load breakup temperature data: {e}"},
            }

        station_name = data.get("meta", {}).get(
            "name",
            STATION_OPTIONS.get(self.station_id, self.station_id),
        )
        
        lat = data.get("meta", {}).get("ll", [None, None])[1]
        lon = data.get("meta", {}).get("ll", [None, None])[0]

        dates = []
        obs_min = []
        obs_max = []
        normal_min = []
        normal_max = []

        for row in data.get("data", []):
            if len(row) < 5:
                continue

            dates.append(row[0])
            obs_max.append(clean_value(row[1]))
            obs_min.append(clean_value(row[2]))
            normal_max.append(clean_value(row[3]))
            normal_min.append(clean_value(row[4]))

        record_max_by_mmdd = {}
        record_min_by_mmdd = {}

        smry = records.get("smry", [])

        if len(smry) >= 2:
            for item in smry[0]:
                if len(item) >= 2 and item[1]:
                    mmdd = item[1][5:10]
                    record_max_by_mmdd[mmdd] = clean_value(item[0])

            for item in smry[1]:
                if len(item) >= 2 and item[1]:
                    mmdd = item[1][5:10]
                    record_min_by_mmdd[mmdd] = clean_value(item[0])

        record_max = []
        record_min = []

        for d in dates:
            mmdd = d[5:10]
            record_max.append(record_max_by_mmdd.get(mmdd))
            record_min.append(record_min_by_mmdd.get(mmdd))
            
                    
        forecast_dates, forecast_min, forecast_max, nbm_basistime = fetch_nbm_temperature_ranges(
            self.station_id,
            forecast=(
                datetime.utcnow() + timedelta(hours=6)
            ).strftime("%Y-%m-%d %H:00"),
        )
        
        nws_dates, nws_min, nws_max = fetch_nws_forecast_temperature_ranges(lat, lon)
        
        cutoff_date = (datetime.utcnow() - timedelta(hours=24)).date()

        def keep_after_cutoff(dates_in, mins_in, maxs_in):
            kept_dates, kept_min, kept_max = [], [], []

            for d, mn, mx in zip(dates_in, mins_in, maxs_in):
                d_date = datetime.strptime(d, "%Y-%m-%d").date()

                if d_date >= cutoff_date + timedelta(days=2):
                    kept_dates.append(d)
                    kept_min.append(mn)
                    kept_max.append(mx)

            return kept_dates, kept_min, kept_max


        forecast_dates, forecast_min, forecast_max = keep_after_cutoff(
            forecast_dates, forecast_min, forecast_max
        )

        nws_dates, nws_min, nws_max = keep_after_cutoff(
            nws_dates, nws_min, nws_max
        )

        return {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": dates,
                    "y": record_max,
                    "name": "Record Max",
                    "line": {"color": "red", "width": 1},
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": dates,
                    "y": normal_max,
                    "name": "Record Max Range",
                    "fill": "tonexty",
                    "fillcolor": "rgba(255, 0, 0, 0.20)",
                    "line": {"color": "rgba(255,255,255,0)", "width": 0},
                    "showlegend": False,
                    "hoverinfo": "skip",
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": dates,
                    "y": normal_max,
                    "name": "Normal Max Temp",
                    "line": {"color": "#B8860B", "width": 1},
                    "showlegend": False,
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": dates,
                    "y": normal_min,
                    "name": "Normal temperature range",
                    "fill": "tonexty",
                    "fillcolor": "rgba(218,165,32,0.45)",
                    "line": {"color": "#B8860B", "width": 1},
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": dates,
                    "y": record_min,
                    "name": "Record Min Range",
                    "fill": "tonexty",
                    "fillcolor": "rgba(0, 255, 255, 0.18)",
                    "line": {"color": "rgba(255,255,255,0)", "width": 0},
                    "showlegend": False,
                    "hoverinfo": "skip",
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": dates,
                    "y": record_min,
                    "name": "Record Min",
                    "line": {"color": "#0099FF", "width": 1},
                },
                {
                    "type": "candlestick",
                    "x": dates,
                    "open": obs_min,
                    "close": obs_max,
                    "low": obs_min,
                    "high": obs_max,
                    "name": "Observed temp range",
                    "increasing": {
                        "line": {"color": "blue", "width": 1},
                        "fillcolor": "blue",
                    },
                    "decreasing": {
                        "line": {"color": "blue", "width": 1},
                        "fillcolor": "blue",
                    },
                    "whiskerwidth": 0,
                },                
               
                {
                    "type": "candlestick",

                    "x": forecast_dates,

                    "open": forecast_min,
                    "close": forecast_max,
                    "low": forecast_min,
                    "high": forecast_max,

                    "name": f"NBM Temps {nbm_basistime}" if nbm_basistime else "NBM Temps",

                    "increasing": {
                        "line": {"color": "red", "width": 1},
                        "fillcolor": "red",
                    },

                    "decreasing": {
                        "line": {"color": "red", "width": 1},
                        "fillcolor": "red",
                    },

                    "whiskerwidth": 0,
                },
                
                                {
                    "type": "candlestick",
                    "x": nws_dates,
                    "open": nws_min,
                    "close": nws_max,
                    "low": nws_min,
                    "high": nws_max,
                    "name": "Current NWS Forecast",
                    "increasing": {
                        "line": {"color": "#3b1f0f", "width": 1},
                        "fillcolor": "#3b1f0f",
                    },
                    "decreasing": {
                        "line": {"color": "#3b1f0f", "width": 1},
                        "fillcolor": "#3b1f0f",
                    },
                    "whiskerwidth": 0,
                },
            ],
            "layout": {
                "title": f"Breakup Temperature Outlooks - {station_name}",

                "xaxis": {
                    "title": "Date",
                    "rangeslider": {"visible": False},
                },

                "yaxis": {"title": "Temperature (°F)"},

                "hovermode": "x unified",

                "bargap": 0,

                "legend": {"orientation": "h", "x": 0, "y": -0.25},

                "margin": {"l": 60, "r": 40, "t": 70, "b": 80},

                "shapes": [
                    {
                        "type": "line",
                        "xref": "x",
                        "yref": "paper",
                        "x0": (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"),
                        "x1": (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"),
                        "y0": 0,
                        "y1": 1,
                        "line": {
                            "color": "black",
                            "width": 2,
                            "dash": "dash",
                        },
                    },

                    *([
                        {
                            "type": "line",
                            "xref": "paper",
                            "yref": "y",
                            "x0": 0,
                            "x1": 1,
                            "y0": 32,
                            "y1": 32,
                            "line": {
                                "color": "royalblue",
                                "width": 2,
                                "dash": "dash",
                            },
                        }
                    ] if SHOW_FREEZING_LINE else []),
                ],
            },
        }