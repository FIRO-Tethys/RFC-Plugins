from intake.source import base

from .utilities import (
    get_ndfd_region_dropdown,
    get_ndfd_product_dropdown,
    get_ndfd_time_dropdown,
    get_ndfd_product_config,
    select_ndfd_time,
    NDFD_VIEW_CONFIG,
)


class RFCNDFDViewer(base.DataSource):
    container = "python"
    version = "0.0.2"
    name = "rfc_ndfd_viewer"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "NDFD Forecast Maps"
    visualization_type = "map"
    visualization_description = "NDFD precipitation and snow forecast map layers from NOAA/NWS WMS services."
    visualization_tags = ["rfc", "weather", "ndfd", "qpf", "snow", "forecast", "wms", "noaa", "map"]
    visualization_attribution = "NOAA / National Weather Service"

    visualization_args = {
        "region": get_ndfd_region_dropdown(),
        "product": get_ndfd_product_dropdown(),
        "time_choice": get_ndfd_time_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, region="APRFC", product="qpf", time_choice="latest", metadata=None, **kwargs):
        self.region = region
        self.product = product
        self.time_choice = time_choice
        super().__init__(metadata=metadata)

    def read(self):
        cfg = get_ndfd_product_config(self.product)
        selected_time = select_ndfd_time(self.product, self.time_choice)

        view = NDFD_VIEW_CONFIG.get(
            self.region,
            {"center": [-16500000, 8500000], "zoom": 3.8},
        )

        wms_params = {
            "LAYERS": cfg["layer"],
            "STYLES": "",
            "FORMAT": "image/png",
            "TRANSPARENT": "true",
            "VERSION": "1.3.0",
        }

        if selected_time:
            wms_params["TIME"] = selected_time

        legend_url = (
            f"{cfg['wms_url']}?REQUEST=GetLegendGraphic"
            f"&VERSION=1.3.0"
            f"&FORMAT=image/png"
            f"&LAYER={cfg['layer']}"
        )

        return {
            "baseMap": "https://server.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer",
            "layers": [
                {
                    "configuration": {
                        "type": "ImageLayer",
                        "props": {
                            "name": f"{cfg['label']} - {selected_time}",
                            "legendUrl": legend_url,
                            "source": {
                                "type": "WMS",
                                "props": {
                                    "url": cfg["wms_url"],
                                    "params": wms_params,
                                },
                            },
                        },
                    }
                }
            ],
            "layerControl": True,
            "map_extent": {
                "extent": f"{view['center'][0]},{view['center'][1]},{view['zoom']}"
            },
        }