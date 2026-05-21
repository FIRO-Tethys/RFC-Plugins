from intake.source import base


HAWAII_FORECAST_BASE_URL = (
    "https://www.weather.gov/images/aprfc/Hawaii_forecasts"
)


HAWAII_STATIONS = {
    "WRVH1": "Waimea River at Waimea River (WRVH1)",
    "HLEH1": "Hanalei River near Hanalei (HLEH1)",
    "WSFH1": "Wailua River near Lihue (WSFH1)",
    "MNWH1": "Manoa Stream at Woodlawn Drive (MNWH1)",
    "OPAH1": "Opaeula Stream near Wahiawa (OPAH1)",
    "WWKH1": "West Wailuaiki Stream near Hana (WWKH1)",
    "NLIH1": "Honolii Stream near Papaikou (NLIH1)",
    "WLUH1": "Wailuku River at Piihonoua (WLUH1)",
}


FORECAST_RUNS = {
    "0": "Current Forecast",
    "6": "Previous Forecast Run (6-hr)",
    "12": "Previous Forecast Run (12-hr)",
    "18": "Previous Forecast Run (18-hr)",
}


def get_hawaii_station_dropdown():
    return [
        {"label": label, "value": sid}
        for sid, label in HAWAII_STATIONS.items()
    ]


def get_hawaii_forecast_run_dropdown():
    return [
        {"label": label, "value": sid}
        for sid, label in FORECAST_RUNS.items()
    ]


class APRFCHawaiiRFCForecastsViewer(base.DataSource):
    container = "python"
    version = "0.0.7"
    name = "aprfc_hawaii_rfc_forecasts"

    visualization_group = "Additional Info"
    visualization_label = "Hawaii RFC Forecasts"
    visualization_type = "image"

    visualization_args = {
        "station": get_hawaii_station_dropdown(),
        "forecast_run": get_hawaii_forecast_run_dropdown(),
    }

    visualization_description = (
        "Experimental Hawaii RFC short-range forecast images from APRFC."
    )

    visualization_tags = [
        "aprfc",
        "hawaii",
        "rfc",
        "forecast",
        "short range",
        "image",
    ]

    visualization_attribution = "NOAA / NWS / APRFC"

    loading_icon = False
    _user_parameters = []

    def __init__(
        self,
        station="WRVH1",
        forecast_run="0",
        metadata=None,
        **kwargs,
    ):
        from rfc_plugins.additional_info import validate_dependencies

        validate_dependencies()

        self.station = station
        self.forecast_run = str(forecast_run)

        super().__init__(metadata=metadata)

    def read(self):
        image_url = (
            f"{HAWAII_FORECAST_BASE_URL}/"
            f"{self.station}.shortrange_{self.forecast_run}.png"
        )

        print(
            f"[APRFCHawaiiRFCForecastsViewer] "
            f"Resolved image URL: {image_url} "
            f"(station={self.station}, "
            f"forecast_run={self.forecast_run})"
        )

        return image_url