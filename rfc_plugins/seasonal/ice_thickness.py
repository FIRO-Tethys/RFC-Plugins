from intake.source import base

from .utilities import (
    get_ice_thickness_month_dropdown,
    get_ice_thickness_year_dropdown,
    get_ice_thickness_product_dropdown,
    fetch_aprfc_ice_thickness_geojson,
)


class APRFCIceThicknessViewer(base.DataSource):
    container = "python"
    version = "0.0.2"
    name = "aprfc_ice_thickness"

    visualization_group = "Seasonal Interest"
    visualization_label = "Ice Thickness"
    visualization_type = "map"
    visualization_description = "APRFC Alaska ice thickness observations."
    visualization_tags = ["aprfc", "seasonal", "ice thickness", "map"]
    visualization_attribution = "NOAA / NWS / APRFC"

    visualization_args = {
        "month": get_ice_thickness_month_dropdown(),
        "year": get_ice_thickness_year_dropdown(),
        "product": get_ice_thickness_product_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(
        self,
        month="03",
        year="2026",
        product="ice",
        metadata=None,
        **kwargs,
    ):
        from rfc_plugins.seasonal import validate_dependencies

        validate_dependencies()
        self.month = str(month).zfill(2)
        self.year = str(year)
        self.product = str(product)

        super().__init__(metadata=metadata)

    def read(self):
        ice_geojson = fetch_aprfc_ice_thickness_geojson(
            month=self.month,
            year=self.year,
            product=self.product,
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
                            "name": "APRFC Ice Thickness",
                            "popup": {
                                "title": "{name}",
                                "content": (
                                    "<b>Station ID:</b> {lid}<br>"
                                    "<b>Year:</b> {year}<br>"
                                    "<b>Month:</b> {month}<br>"
                                    "<b>Elevation:</b> {elev}<br>"
                                    "<b>Ice thickness:</b> {ice} in<br>"
                                    "<b>Date:</b> {date}<br>"
                                    "<b>Monthly average:</b> {avg} in<br>"
                                    "<b>Ice thickness % avg:</b> {percent_avg}%<br>"
                                    "<b>Average sample count:</b> {avg_count}"
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