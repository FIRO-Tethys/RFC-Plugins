from intake.source import base

from .utilities import (
    get_radar_region_dropdown,
    get_radar_product_dropdown,
    fetch_radar_stations_geojson,
    build_selected_location_geojson,
    get_latest_hazard_time,
)


class RFCRadarViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "rfc_radar_viewer"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "Radar"
    visualization_type = "map"
    visualization_description = "NWS radar and warning map layers for RFC regions."
    visualization_tags = ["rfc", "weather", "radar", "warnings", "nws", "noaa", "map"]
    visualization_attribution = "NOAA / National Weather Service"

    visualization_args = {
        "region": get_radar_region_dropdown(),
        "product": get_radar_product_dropdown(),
    }

    def __init__(self, region="APRFC", product="alaska_bref_qcd", metadata=None):
        self.region = region
        self.product = product
        super().__init__(metadata=metadata)

    def read(self):
        if self.product == "local":
            return self._local_radar_map()

        if self.product == "alerts":
            return self._alerts_map()

        return self._national_radar_map()

    def _national_radar_map(self):
        return {
            "baseMap": "https://server.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer",
            "layers": [
                {
                    "configuration": {
                        "type": "ImageLayer",
                        "props": {
                            "name": "National Radar - Alaska Mosaic",
                            "source": {
                                "type": "WMS",
                                "props": {
                                    "url": "https://opengeo.ncep.noaa.gov/geoserver/alaska/alaska_bref_qcd/ows",
                                    "params": {
                                        "LAYERS": "alaska_bref_qcd",
                                        "FORMAT": "image/png",
                                        "TRANSPARENT": "true",
                                    },
                                },
                            },
                        },
                    }
                }
            ],
            "layerControl": True,
            "map_extent": {"extent": "-16500000,8500000,4.5"},
        }

    def _local_radar_map(self):
        radar_stations_geojson = fetch_radar_stations_geojson()
        radar_stations_geojson["crs"] = {"properties": {"name": "EPSG:4326"}}

        return {
            "baseMap": "https://server.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer",
            "layers": [
                {
                    "configuration": {
                        "type": "VectorLayer",
                        "props": {
                            "name": "Local Radar Stations",
                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": radar_stations_geojson,
                            },
                        },
                    }
                }
            ],
            "layerControl": True,
            "map_extent": {"extent": "-16500000,8500000,4.5"},
        }

    def _alerts_map(self):
        location_geojson = build_selected_location_geojson(
            lon=-151.35,
            lat=60.73,
            name="Selected Location",
        )
        
        hazard_time = get_latest_hazard_time()

        return {
            "baseMap": "https://server.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer",
            "layers": [
                {
                    "configuration": {
                        "type": "ImageLayer",
                        "props": {
                            "name": "NWS Warnings / Hazards",
                            "source": {
                                "type": "WMS",
                                "props": {
                                    "url": "https://opengeo.ncep.noaa.gov/geoserver/wwa/hazards/ows",
                                    "params": {
                                        "LAYERS": "warnings",
                                        "FORMAT": "image/png",
                                        "TRANSPARENT": "true",
                                        "TILED": "true",
                                        "TIME": hazard_time,
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
                            "name": "Selected Location",
                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": location_geojson,
                            },
                        },
                    }
                },
            ],
            "layerControl": True,
            "map_extent": {"extent": "-16500000,8500000,4.5"},
        }