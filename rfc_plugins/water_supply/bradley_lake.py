from intake.source import base


BRADLEY_BASE_URL = "https://www.weather.gov"


BRADLEY_PRODUCT_OPTIONS = {
    "weekly_volume": {
        "label": "Bradley Lake Weekly Inflow Volume",
        "path": "/images/aprfc/bradley/bradleyweekly/BRIN.volume.hefs.png",
    },
    "daily_inflow": {
        "label": "Bradley Lake Daily Inflow Forecast",
        "path": "/images/aprfc/bradley/bradleydaily/BRIN.shortrange.hefs.png",
    },
    "bcda2_daily": {
        "label": "BCDA2 Daily Forecast",
        "path": "/images/aprfc/bradley/bradleydaily/BCDA2.shortrange.hefs.png",
    },
}


def get_bradley_product_dropdown():
    return [
        {"label": cfg["label"], "value": key}
        for key, cfg in BRADLEY_PRODUCT_OPTIONS.items()
    ]


class APRFCBradleyLakeViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_bradley_lake"

    visualization_group = "Water Supply"
    visualization_label = "Bradley Lake"
    visualization_type = "image"

    visualization_args = {
        "product": get_bradley_product_dropdown(),
    }

    visualization_description = "APRFC Bradley Lake inflow forecast static images."
    visualization_tags = ["aprfc", "water supply", "bradley lake", "inflow", "image"]
    visualization_attribution = "NOAA / NWS / APRFC"

    loading_icon = False
    _user_parameters = []

    def __init__(self, product="weekly_volume", metadata=None, **kwargs):
        from rfc_plugins.water_supply import validate_dependencies

        validate_dependencies()
        self.product = product
        super().__init__(metadata=metadata)

    def read(self):
        product_cfg = BRADLEY_PRODUCT_OPTIONS.get(
            self.product,
            BRADLEY_PRODUCT_OPTIONS["weekly_volume"],
        )

        image_url = f"{BRADLEY_BASE_URL}{product_cfg['path']}"

        print(
            f"[APRFCBradleyLakeViewer] Resolved image URL: {image_url} "
            f"(product={self.product})"
        )

        return image_url