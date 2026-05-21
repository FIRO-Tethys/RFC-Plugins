from intake.source import base


HEFS_BASE_URL = "https://water.noaa.gov/resources/probabilistic/short_term"


HEFS_SITE_OPTIONS = {
    "SRYA2": "Situk River nr Yakutat (SRYA2)",
    "CKTA2": "Chilkat River at Klukwan (CKTA2)",
    "MNDA2": "Mendenhall Lake (MNDA2)",
    "TKUA2": "Taku River nr Juneau (TKUA2)",
    "SCKA2": "Staney Creek nr Klawock (SCKA2)",
    "CHLA2": "Little Chena River nr Fairbanks (CHLA2)",
    "UCHA2": "Chena River nr Two Rivers (UCHA2)",
    "CRHA2": "Chena River blw Hunts Creek (CRHA2)",
    "GBDA2": "Goodpaster River nr Big Delta (GBDA2)",
    "SIXA2": "Sixmile Creek nr Hope (SIXA2)",
    "SNOA2": "Snow River nr Seward (SNOA2)",
    "MPTA2": "Trail River nr Lawing (MPTA2)",
    "COOA2": "Kenai River at Cooper Landing (COOA2)",
}


def get_hefs_site_dropdown():
    return [
        {"label": label, "value": site_id}
        for site_id, label in HEFS_SITE_OPTIONS.items()
    ]


class APRFCHEFSPlotsViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_hefs_plots"

    visualization_group = "River Observations and Forecasts"
    visualization_label = "HEFS Plots"
    visualization_type = "image"

    visualization_args = {
        "site": get_hefs_site_dropdown(),
    }

    visualization_description = (
        "APRFC operational HEFS short-range probabilistic forecast plots."
    )
    visualization_tags = ["aprfc", "river", "hefs", "probabilistic", "forecast", "image"]
    visualization_attribution = "NOAA / NWS / APRFC / water.noaa.gov"

    loading_icon = False
    _user_parameters = []

    def __init__(self, site="SRYA2", metadata=None, **kwargs):
        from rfc_plugins.river import validate_dependencies

        validate_dependencies()
        self.site = site
        super().__init__(metadata=metadata)

    def read(self):
        image_url = f"{HEFS_BASE_URL}/{self.site}.shortrange.hefs.png"

        print(
            f"[APRFCHEFSPlotsViewer] Resolved image URL: {image_url} "
            f"(site={self.site})"
        )

        return image_url