from intake.source import base

from .utilities import (
    get_fdd_station_dropdown,
    fetch_acis_fdd_daily_series,
)


class RFCFreezingDegreeDaysTimeSeries(base.DataSource):
    container = "python"
    version = "0.0.2"
    name = "rfc_fdd_timeseries"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "Freezing Degree Days - Time Series"
    visualization_type = "plotly"
    visualization_description = "Freezing Degree Day time series from RCC-ACIS."
    visualization_tags = ["rfc", "weather", "fdd", "freezing degree days", "timeseries", "acis"]
    visualization_attribution = "RCC-ACIS"

    visualization_args = {
        "station_id": get_fdd_station_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, station_id="pabr", metadata=None, **kwargs):
        from rfc_plugins.weather import validate_dependencies
        validate_dependencies()
        self.station_id = station_id
        super().__init__(metadata=metadata)

    def read(self):
        result = fetch_acis_fdd_daily_series(self.station_id)

        if not result["data"]:
            return {
                "data": [],
                "layout": {
                    "title": f"No FDD data returned for {self.station_id}",
                },
            }

        dates = [row["date"] for row in result["data"]]
        daily_fdd = [row["daily_fdd"] for row in result["data"]]
        cumulative_fdd = [row["cumulative_fdd"] for row in result["data"]]

        return {
            "data": [
                {
                    "type": "bar",
                    "x": dates,
                    "y": daily_fdd,
                    "name": "Daily FDD",
                    "yaxis": "y1",
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": dates,
                    "y": cumulative_fdd,
                    "name": "Cumulative FDD",
                    "yaxis": "y2",
                },
            ],
            "layout": {
                "title": f"Freezing Degree Days - {result['station_name']}",
                "xaxis": {"title": "Date"},
                "yaxis": {"title": "Daily FDD"},
                "yaxis2": {
                    "title": "Cumulative FDD",
                    "overlaying": "y",
                    "side": "right",
                },
                "legend": {"orientation": "h", "x": 0, "y": -0.2},
                "hovermode": "x unified",
            },
        }