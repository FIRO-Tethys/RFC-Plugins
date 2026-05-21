from intake.source import base


SNOW_LEVEL_BASE_URL = "https://www.weather.gov/images/aprfc/qpf-qpe-maps"


SNOW_LEVEL_FRAME_OPTIONS = {
    "1": "Frame 1",
    "2": "Frame 2",
    "3": "Frame 3",
    "4": "Frame 4",
    "5": "Frame 5",
    "6": "Frame 6",
    "7": "Frame 7",
    "8": "Frame 8",
    "9": "Frame 9",
    "10": "Frame 10",
    "11": "Frame 11",
    "12": "Frame 12",
    "13": "Frame 13",
    "14": "Frame 14",
    "15": "Frame 15",
    "16": "Frame 16",
    "17": "Frame 17",
    "18": "Frame 18",
    "19": "Frame 19",
    "20": "Frame 20",
    "21": "Frame 21",
    "22": "Frame 22",
    "23": "Frame 23",
    "24": "Frame 24",
    "25": "Frame 25",
    "26": "Frame 26",
    "27": "Frame 27",
    "28": "Frame 28",
    "29": "Frame 29",
    "30": "Frame 30",
    "31": "Frame 31",
    "32": "Frame 32",
}


def get_snow_level_frame_dropdown():
    return [
        {"label": label, "value": frame_id}
        for frame_id, label in SNOW_LEVEL_FRAME_OPTIONS.items()
    ]


class APRFCNBMSnowLevelForecastViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_nbm_snow_level_forecast"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "NBM Snow Level Forecast"
    visualization_type = "image"

    visualization_args = {
        "frame": get_snow_level_frame_dropdown(),
    }

    visualization_description = (
        "APRFC NBM 8-day snow level forecast static image frames."
    )
    visualization_tags = [
        "aprfc",
        "weather",
        "snow level",
        "nbm",
        "forecast",
        "image",
    ]
    visualization_attribution = "NOAA / NWS / APRFC"

    loading_icon = False
    _user_parameters = []

    def __init__(self, frame="1", metadata=None, **kwargs):
        from rfc_plugins.weather import validate_dependencies

        validate_dependencies()
        self.frame = str(frame)
        super().__init__(metadata=metadata)

    def read(self):
        image_url = f"{SNOW_LEVEL_BASE_URL}/snowlevel_{self.frame}.png"

        print(
            f"[APRFCNBMSnowLevelForecastViewer] Resolved image URL: {image_url} "
            f"(frame={self.frame})"
        )

        return image_url