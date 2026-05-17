from intake.source import base
from urllib.parse import quote

from .utilities import (
    get_mrms_region_dropdown,
    get_mrms_product_dropdown,
)


class RFCMRMSViewer(base.DataSource):
    container = "python"
    version = "0.0.5"
    name = "rfc_mrms_viewer"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "MRMS QPE"
    visualization_type = "image"

    visualization_description = "MRMS QPE image products from NOAA/NWS ImageServer."
    visualization_tags = ["rfc", "weather", "mrms", "qpe", "precipitation", "noaa", "image"]
    visualization_attribution = "NOAA / National Weather Service"

    visualization_args = {
        "region": get_mrms_region_dropdown(),
        "product": get_mrms_product_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, region="APRFC", product="rft_24hr", metadata=None, **kwargs):
        self.region = region
        self.product = product
        super().__init__(metadata=metadata)

    def read(self):
        rendering_rule = quote(f'{{"rasterFunction":"{self.product}"}}')

        return (
            "https://mapservices.weather.noaa.gov/raster/rest/services/obs/"
            "mrms_qpe/ImageServer/exportImage"
            "?f=image"
            "&format=png"
            "&transparent=true"
            "&bbox=-19592230,1118019,-6678388,11753184"
            "&bboxSR=3857"
            "&imageSR=3857"
            "&size=1200,900"
            f"&renderingRule={rendering_rule}"
        )