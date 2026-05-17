from intake.source import base

from .utilities import (
    get_precip_region_dropdown,
    get_precip_dataset_dropdown,
    get_precip_product_dropdown,
    get_precip_layer_id,
    get_precip_wms_url,
    get_precip_product_label,
    PRECIP_VIEW_CONFIG,
)


class RFCPrecipViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "rfc_precip_viewer"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "QPE / QPF Viewer"
    visualization_type = "map"
    visualization_description = "RFC QPE and WPC QPF precipitation map layers from NOAA/NWS WMS services."
    visualization_tags = ["rfc", "weather", "qpe", "qpf", "precipitation", "wms", "noaa", "map"]
    visualization_attribution = "NOAA / National Weather Service"

    visualization_args = {
        "region": get_precip_region_dropdown(),
        "dataset": get_precip_dataset_dropdown(),
        "product": get_precip_product_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, region="APRFC", dataset="qpe", product="last_10d", metadata=None, **kwargs):
        self.region = region
        self.dataset = dataset
        self.product = product
        super().__init__(metadata=metadata)

    def read(self):
        layer_id = get_precip_layer_id(self.dataset, self.product)
        wms_url = get_precip_wms_url(self.dataset)
        product_label = get_precip_product_label(self.dataset, self.product)

        view = PRECIP_VIEW_CONFIG.get(
            self.region,
            {"center": [-16500000, 8500000], "zoom": 3.8},
        )

        legend_url = (
            f"{wms_url}?REQUEST=GetLegendGraphic"
            f"&VERSION=1.3.0"
            f"&FORMAT=image/png"
            f"&LAYER={layer_id}"
        )

        return {
            "baseMap": "https://server.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer",
            "layers": [
                {
                    "configuration": {
                        "type": "ImageLayer",
                        "props": {
                            "name": product_label,
                            "legendUrl": legend_url,
                            "source": {
                                "type": "WMS",
                                "props": {
                                    "url": wms_url,
                                    "params": {
                                        "LAYERS": layer_id,
                                        "STYLES": "",
                                        "FORMAT": "image/png",
                                        "TRANSPARENT": "true",
                                        "VERSION": "1.3.0",
                                    },
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