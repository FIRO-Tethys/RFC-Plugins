# from intake.source import base

# from .utilities import (
#     get_radar_region_dropdown,
# )


# class RFCWeatherForecastsViewer(base.DataSource):
#     container = "python"
#     version = "0.0.1"
#     name = "rfc_weather_forecasts"

#     visualization_group = "Weather Observations and Forecasts"
#     visualization_label = "Weather Forecasts"
#     visualization_type = "map"

#     visualization_description = (
#         "NWS Watches, Warnings, and Advisories map."
#     )

#     visualization_tags = [
#         "weather",
#         "forecast",
#         "warnings",
#         "advisories",
#         "nws",
#         "noaa",
#         "wms",
#     ]

#     visualization_attribution = "NOAA / National Weather Service"

#     visualization_args = {
#         "region": get_radar_region_dropdown(),
#     }

#     loading_icon = False
#     _user_parameters = []

#     def __init__(self, region="APRFC", metadata=None, **kwargs):
#         self.region = region
#         super().__init__(metadata=metadata)

#     def read(self):

#         return {
#             "baseMap": (
#                 "https://server.arcgisonline.com/arcgis/rest/services/"
#                 "Canvas/World_Light_Gray_Base/MapServer"
#             ),
#             "layers": [
#                 {
#                     "configuration": {
#                         "type": "ImageLayer",
#                         "props": {
#                             "name": "NWS Watches Warnings Advisories",
#                             "source": {
#                                 "type": "WMS",
#                                 "props": {
#                                     "url": (
#                                         "https://mapservices.weather.noaa.gov/"
#                                         "eventdriven/services/WWA/"
#                                         "watch_warn_adv/MapServer/WMSServer"
#                                     ),
#                                     "params": {
#                                         "LAYERS": "0",
#                                         "FORMAT": "image/png",
#                                         "TRANSPARENT": "true",
#                                         "VERSION": "1.3.0",
#                                     },
#                                 },
#                             },
#                         },
#                     }
#                 }
#             ],
#             "layerControl": True,
#             "map_extent": {
#                 "extent": "-16500000,8500000,3.8"
#             },
#         }

from intake.source import base

from .utilities import (
    get_radar_region_dropdown,
    fetch_wwa_arcgis_geojson,
)


class RFCWeatherForecastsViewer(base.DataSource):
    container = "python"
    version = "0.0.2"
    name = "rfc_weather_forecasts"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "Weather Forecasts"
    visualization_type = "map"

    visualization_description = "NWS Watches, Warnings, and Advisories map."
    visualization_tags = ["weather", "forecast", "warnings", "advisories", "nws", "noaa", "wms"]
    visualization_attribution = "NOAA / National Weather Service"

    visualization_args = {
        "region": get_radar_region_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, region="APRFC", metadata=None, **kwargs):
        self.region = region
        super().__init__(metadata=metadata)

    def read(self):
        wms_url = (
            "https://mapservices.weather.noaa.gov/eventdriven/services/WWA/"
            "watch_warn_adv/MapServer/WMSServer"
        )

        legend_url = (
            f"{wms_url}?REQUEST=GetLegendGraphic"
            f"&VERSION=1.3.0"
            f"&FORMAT=image/png"
            f"&LAYER=0"
        )

        alerts_geojson = fetch_wwa_arcgis_geojson()

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
                            "name": "NWS Watches Warnings Advisories",
                            "legendUrl": legend_url,
                            "source": {
                                "type": "WMS",
                                "props": {
                                    "url": wms_url,
                                    "params": {
                                        "LAYERS": "0",
                                        "FORMAT": "image/png",
                                        "TRANSPARENT": "true",
                                        "VERSION": "1.3.0",
                                    },
                                },
                            },
                        },
                    }
                },
                {
                    "configuration": {
                        "type": "VectorLayer",
                        "props": {
                            "name": "Clickable Active Alerts",
                            "popup": {
                                "title": "{event}",
                                "content": (
                                    "<b>Headline:</b> {headline}<br>"
                                    "<b>Area:</b> {areaDesc}"
                                ),
                            },
                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": alerts_geojson,
                            },
                        },
                    }
                },
            ],
            "layerControl": True,
            "map_extent": {
                "extent": "-16500000,8500000,3.8"
            },
        }