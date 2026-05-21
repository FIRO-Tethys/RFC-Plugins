from intake.source import base


FREEZE_LEVEL_BASE_URL = "https://www.weather.gov/images/aprfc/qpf-qpe-maps"


FREEZE_LEVEL_FRAME_OPTIONS = {
    "00": "Frame 00",
    "01": "Frame 01",
    "02": "Frame 02",
    "03": "Frame 03",
    "04": "Frame 04",
    "05": "Frame 05",
    "06": "Frame 06",
    "07": "Frame 07",
    "08": "Frame 08",
    "09": "Frame 09",
    "10": "Frame 10",
    "11": "Frame 11",
    "12": "Frame 12",
}


def get_freeze_level_frame_dropdown():
    return [
        {"label": label, "value": frame_id}
        for frame_id, label in FREEZE_LEVEL_FRAME_OPTIONS.items()
    ]


class APRFCFreezeLevelMapsViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_freeze_level_maps"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "Freeze Level Maps"
    visualization_type = "image"

    visualization_args = {
        "frame": get_freeze_level_frame_dropdown(),
    }

    visualization_description = "APRFC freezing level map static image frames."
    visualization_tags = [
        "aprfc",
        "weather",
        "freeze level",
        "freezing level",
        "forecast",
        "image",
    ]
    visualization_attribution = "NOAA / NWS / APRFC"

    loading_icon = False
    _user_parameters = []

    def __init__(self, frame="00", metadata=None, **kwargs):
        from rfc_plugins.weather import validate_dependencies

        validate_dependencies()
        self.frame = str(frame).zfill(2)
        super().__init__(metadata=metadata)

    def read(self):
        image_url = f"{FREEZE_LEVEL_BASE_URL}/fzlevels_{self.frame}.png"

        print(
            f"[APRFCFreezeLevelMapsViewer] Resolved image URL: {image_url} "
            f"(frame={self.frame})"
        )

        return image_url