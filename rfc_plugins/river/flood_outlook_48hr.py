from intake.source import base


APRFC_48HR_FLOOD_OUTLOOK_URL = (
    "https://www.weather.gov/images/aprfc/qpf-qpe-maps/48flood_pot.gif"
)


class APRFCFloodOutlook48hrViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_48hr_flood_outlook"

    visualization_group = "River Observations and Forecasts"
    visualization_label = "48hr Flood Outlook"
    visualization_type = "image"
    visualization_description = "APRFC 48-Hour Flood Outlook static image."
    visualization_tags = ["aprfc", "river", "flood", "outlook", "48hr", "image"]
    visualization_attribution = "NOAA / NWS / APRFC"

    visualization_args = {}

    loading_icon = False
    _user_parameters = []

    def __init__(self, metadata=None, **kwargs):
        from rfc_plugins.river import validate_dependencies

        validate_dependencies()
        super().__init__(metadata=metadata)

    def read(self):
        image_url = APRFC_48HR_FLOOD_OUTLOOK_URL
        print(f"[APRFCFloodOutlook48hrViewer] Resolved image URL: {image_url}")
        return image_url