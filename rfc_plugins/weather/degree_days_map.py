from intake.source import base

from .utilities import (
    get_fdd_region_dropdown,
    fetch_aprfc_fdd_map_geojson,
    FDD_VIEW_CONFIG,
)


class RFCFreezingDegreeDaysMap(base.DataSource):
    container = "python"
    version = "0.0.3"
    name = "rfc_fdd_map"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "Freezing Degree Days - Station Map"
    visualization_type = "map"
    visualization_description = "APRFC Freezing Degree Day station map from RCC-ACIS."
    visualization_tags = ["rfc", "weather", "fdd", "freezing degree days", "map", "acis"]
    visualization_attribution = "NOAA / APRFC / RCC-ACIS"

    visualization_args = {
        "region": get_fdd_region_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, region="APRFC", metadata=None, **kwargs):
        from rfc_plugins.weather import validate_dependencies
        validate_dependencies()
        self.region = region
        super().__init__(metadata=metadata)

    def read(self):
        view = FDD_VIEW_CONFIG.get(
            self.region,
            {"center": [-16500000, 8500000], "zoom": 3.8},
        )

        fdd_geojson = fetch_aprfc_fdd_map_geojson()

        return {
            "baseMap": (
                "https://server.arcgisonline.com/arcgis/rest/services/"
                "Canvas/World_Light_Gray_Base/MapServer"
            ),
            "layers": [
                {
                    "configuration": {
                        "type": "VectorLayer",
                        "props": {
                            "name": "APRFC FDD Stations",
                            "popup": {
                                "title": "{name}",
                                "content": (
                                    "<b>FDD:</b> {fdd}<br>"
                                    "<b>FDD % Normal:</b> {percent_label}<br>"
                                    "<b>Period:</b> {sdate} to {edate}<br>"
                                    "<b>Missing days filled with normal:</b> {missing_count}"
                                ),
                            },
                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": fdd_geojson,
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