from intake.source import base

from .utilities import (
    get_ice_thickness_dataset_dropdown,
    get_ice_thickness_month_dropdown,
    fetch_ice_thickness_geojson,
)


class APRFCIceThicknessViewer(base.DataSource):

    container = "python"
    version = "0.0.1"
    name = "aprfc_ice_thickness"

    visualization_group = "Seasonal Interest"
    visualization_label = "Ice Thickness"
    visualization_type = "map"

    visualization_description = (
        "APRFC ice thickness observation points from APRFC JSON data."
    )

    visualization_tags = [
        "aprfc",
        "seasonal",
        "ice",
        "ice thickness",
        "map",
        "alaska",
    ]

    visualization_attribution = "NOAA / APRFC"

    visualization_args = {
        "dataset": get_ice_thickness_dataset_dropdown(),
        "month": get_ice_thickness_month_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(
        self,
        dataset="current",
        month="all",
        metadata=None,
        **kwargs,
    ):

        self.dataset = dataset
        self.month = month

        super().__init__(metadata=metadata)

    def read(self):

        ice_geojson = fetch_ice_thickness_geojson(
            dataset=self.dataset,
            month=self.month,
        )

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
                            "name": "APRFC Ice Thickness Sites",
                            "popup": {
                                "title": "{name}",
                                "content": (
                                    "<b>Date:</b> {latest_date}<br>"
                                    "<b>Ice Thickness:</b> {ice_thickness}<br>"
                                    "<b>Snow Depth:</b> {snow_depth}<br>"
                                    "<b>Notes:</b> {notes}"
                                ),
                            },
                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": ice_geojson,
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