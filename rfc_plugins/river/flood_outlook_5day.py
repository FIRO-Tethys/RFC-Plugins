from intake.source import base


APRFC_5DAY_FLOOD_OUTLOOK_URL = (
    "https://www.weather.gov/images/aprfc/qpf-qpe-maps/akfop.gif"
)


class APRFCFloodOutlook5DayViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_5day_flood_outlook"

    visualization_group = "River Observations and Forecasts"
    visualization_label = "5 Day Flood Outlook"
    visualization_type = "image"
    visualization_description = "APRFC 5-Day Flood Outlook static image."
    visualization_tags = ["aprfc", "river", "flood", "outlook", "5day", "image"]
    visualization_attribution = "NOAA / NWS / APRFC"

    visualization_args = {}

    loading_icon = False
    _user_parameters = []

    def __init__(self, metadata=None, **kwargs):
        from rfc_plugins.river import validate_dependencies

        validate_dependencies()
        super().__init__(metadata=metadata)

    def read(self):
        image_url = APRFC_5DAY_FLOOD_OUTLOOK_URL
        print(f"[APRFCFloodOutlook5DayViewer] Resolved image URL: {image_url}")
        return image_url