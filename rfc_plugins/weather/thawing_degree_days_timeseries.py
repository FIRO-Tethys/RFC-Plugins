from intake.source import base

from .utilities import (
    get_tdd_station_dropdown,
    fetch_acis_tdd_daily_series,
)


class RFCThawingDegreeDaysTimeSeries(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "rfc_tdd_timeseries"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "Thawing Degree Days - Time Series"
    visualization_type = "plotly"
    visualization_description = "Thawing Degree Day time series from RCC-ACIS."
    visualization_tags = ["rfc", "weather", "tdd", "thawing degree days", "timeseries", "acis"]
    visualization_attribution = "RCC-ACIS"

    visualization_args = {
        "station_id": get_tdd_station_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, station_id="panc", metadata=None, **kwargs):
        from rfc_plugins.weather import validate_dependencies
        validate_dependencies()
        self.station_id = station_id
        super().__init__(metadata=metadata)

    def read(self):
        result = fetch_acis_tdd_daily_series(self.station_id)

        if not result["data"]:
            return {
                "data": [],
                "layout": {"title": f"No TDD data returned for {self.station_id}"},
            }

        dates = [row["date"] for row in result["data"]]
        daily_tdd = [row["daily_tdd"] for row in result["data"]]
        cumulative_tdd = [row["cumulative_tdd"] for row in result["data"]]

        return {
            "data": [
                {
                    "type": "bar",
                    "x": dates,
                    "y": daily_tdd,
                    "name": "Daily TDD",
                    "yaxis": "y1",
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": dates,
                    "y": cumulative_tdd,
                    "name": "Cumulative TDD",
                    "yaxis": "y2",
                },
            ],
            "layout": {
                "title": f"Thawing Degree Days - {result['station_name']}",
                "xaxis": {"title": "Date"},
                "yaxis": {"title": "Daily TDD"},
                "yaxis2": {
                    "title": "Cumulative TDD",
                    "overlaying": "y",
                    "side": "right",
                },
                "legend": {"orientation": "h", "x": 0, "y": -0.2},
                "hovermode": "x unified",
            },
        }