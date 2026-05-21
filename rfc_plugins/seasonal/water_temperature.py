from intake.source import base

from .utilities import fetch_aprfc_water_temperature_geojson


class APRFCWaterTemperatureViewer(base.DataSource):
    container = "python"
    version = "0.0.6"
    name = "aprfc_water_temperature"

    visualization_group = "Seasonal Interest"
    visualization_label = "Water Temperature"
    visualization_type = "map"
    visualization_description = "APRFC Alaska water temperature observations."
    visualization_tags = ["aprfc", "seasonal", "water temperature", "map"]
    visualization_attribution = "NOAA / NWS / APRFC"

    visualization_args = {}

    loading_icon = False
    _user_parameters = []

    def __init__(self, metadata=None, **kwargs):
        from rfc_plugins.seasonal import validate_dependencies
        validate_dependencies()
        super().__init__(metadata=metadata)

    def read(self):
        tw_geojson = fetch_aprfc_water_temperature_geojson()

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
                            "name": "APRFC Water Temperature",
                            "popup": {
                                "title": "{name}",
                                "content": (
                                    "<b>Station ID:</b> {lid}<br>"
                                    "<b>Owner:</b> {owner}<br>"
                                    "<b>Elevation:</b> {elev}<br>"
                                    "<b>Reading:</b> {tw} °F"
                                ),
                            },
                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": tw_geojson,
                            },
                        },
                    }
                }
            ],
            "layerControl": True,
            "map_extent": {
                "extent": "-16500000,8500000,3.8"
            },
        }