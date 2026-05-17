from intake.source import base


CPC_PRODUCT_OPTIONS = {
    "6_10_temp": {
        "label": "CPC 6-10 Day Temperature Outlook",
        "url": "https://mapservices.weather.noaa.gov/vector/services/outlooks/cpc_6_10_day_outlk/MapServer/WMSServer",
        "layer": "0",
    },
    "6_10_precip": {
        "label": "CPC 6-10 Day Precipitation Outlook",
        "url": "https://mapservices.weather.noaa.gov/vector/services/outlooks/cpc_6_10_day_outlk/MapServer/WMSServer",
        "layer": "1",
    },
    "8_14_temp": {
        "label": "CPC 8-14 Day Temperature Outlook",
        "url": "https://mapservices.weather.noaa.gov/vector/services/outlooks/cpc_8_14_day_outlk/MapServer/WMSServer",
        "layer": "0",
    },
    "8_14_precip": {
        "label": "CPC 8-14 Day Precipitation Outlook",
        "url": "https://mapservices.weather.noaa.gov/vector/services/outlooks/cpc_8_14_day_outlk/MapServer/WMSServer",
        "layer": "1",
    },
    "hazards": {
        "label": "CPC/WPC Hazards",
        "url": "https://mapservices.weather.noaa.gov/vector/services/hazards/cpc_weather_hazards/MapServer/WMSServer",
        "layer": "0",
    },
}

REGION_OPTIONS = {
    "APRFC": {"label": "Alaska RFC", "extent": "-16500000,8500000,3.8"},
    "CONUS": {"label": "CONUS", "extent": "-10700000,4700000,4.5"},
}


def get_cpc_product_dropdown():
    return [
        {"label": cfg["label"], "value": key}
        for key, cfg in CPC_PRODUCT_OPTIONS.items()
    ]


def get_cpc_region_dropdown():
    return [
        {"label": cfg["label"], "value": key}
        for key, cfg in REGION_OPTIONS.items()
    ]


class RFCCPCOutlooksViewer(base.DataSource):
    container = "python"
    version = "0.0.2"
    name = "rfc_cpc_outlooks"

    visualization_group = "Climate and History"
    visualization_label = "CPC Outlooks / Predictions"
    visualization_type = "map"

    visualization_description = (
        "CPC temperature, precipitation, and hazard outlook map layers from NOAA/NWS map services."
    )
    visualization_tags = [
        "rfc", "climate", "cpc", "outlooks", "predictions",
        "temperature", "precipitation", "hazards", "wms", "noaa", "map",
    ]
    visualization_attribution = "NOAA / CPC / NWS"

    visualization_args = {
        "region": get_cpc_region_dropdown(),
        "product": get_cpc_product_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, region="APRFC", product="6_10_temp", metadata=None, **kwargs):
        self.region = region
        self.product = product
        super().__init__(metadata=metadata)

    def read(self):
        cfg = CPC_PRODUCT_OPTIONS[self.product]
        region_cfg = REGION_OPTIONS.get(self.region, REGION_OPTIONS["APRFC"])

        legend_url = (
            f"{cfg['url']}?REQUEST=GetLegendGraphic"
            f"&VERSION=1.3.0"
            f"&FORMAT=image/png"
            f"&LAYER={cfg['layer']}"
        )

        return {
            "baseMap": (
                "https://server.arcgisonline.com/arcgis/rest/services/"
                "Canvas/World_Light_Gray_Base/MapServer"
            ),
            "layers": [
                {
                    "configuration": {
                        "type": "ImageLayer",
                        "props": {
                            "name": cfg["label"],
                            "legendUrl": legend_url,
                            "source": {
                                "type": "WMS",
                                "props": {
                                    "url": cfg["url"],
                                    "params": {
                                        "LAYERS": cfg["layer"],
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
            "map_extent": {"extent": region_cfg["extent"]},
        }