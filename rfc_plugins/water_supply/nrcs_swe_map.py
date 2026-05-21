from intake.source import base

from .utilities import (
    get_swe_product_dropdown,
    fetch_aprfc_nrcs_swe_geojson,
)


SWE_RENDERER = {
    "type": "uniqueValue",
    "field": "category",
    "defaultSymbol": {
        "type": "simple-marker",
        "color": [150, 150, 150, 0.8],
        "size": 14,
        "outline": {"color": [0, 0, 0, 0.7], "width": 1},
    },
    "uniqueValueInfos": [
        {"value": "0–6.25 in", "label": "0–6.25 in", "symbol": {"type": "simple-marker", "color": [255, 255, 255, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "6.25–12.5 in", "label": "6.25–12.5 in", "symbol": {"type": "simple-marker", "color": [233, 228, 148, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "12.5–18.75 in", "label": "12.5–18.75 in", "symbol": {"type": "simple-marker", "color": [210, 200, 40, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "18.75–25 in", "label": "18.75–25 in", "symbol": {"type": "simple-marker", "color": [115, 200, 30, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "25–31.25 in", "label": "25–31.25 in", "symbol": {"type": "simple-marker", "color": [20, 200, 20, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "31.25–37.5 in", "label": "31.25–37.5 in", "symbol": {"type": "simple-marker", "color": [10, 140, 138, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "37.5–43.75 in", "label": "37.5–43.75 in", "symbol": {"type": "simple-marker", "color": [0, 80, 255, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "43.75–50 in", "label": "43.75–50 in", "symbol": {"type": "simple-marker", "color": [10, 40, 218, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "50+ in", "label": "50+ in", "symbol": {"type": "simple-marker", "color": [20, 0, 180, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
    ],
}


SWE_PERCENT_RENDERER = {
    "type": "uniqueValue",
    "field": "category",
    "defaultSymbol": {
        "type": "simple-marker",
        "color": [150, 150, 150, 0.8],
        "size": 14,
        "outline": {"color": [0, 0, 0, 0.7], "width": 1},
    },
    "uniqueValueInfos": [
        {"value": "0–25%", "label": "0–25%", "symbol": {"type": "simple-marker", "color": [215, 0, 0, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "25–50%", "label": "25–50%", "symbol": {"type": "simple-marker", "color": [235, 80, 0, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "50–75%", "label": "50–75%", "symbol": {"type": "simple-marker", "color": [255, 160, 0, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "75–100%", "label": "75–100%", "symbol": {"type": "simple-marker", "color": [255, 208, 128, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "100–125%", "label": "100–125%", "symbol": {"type": "simple-marker", "color": [255, 255, 255, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "125–150%", "label": "125–150%", "symbol": {"type": "simple-marker", "color": [143, 238, 143, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "150–175%", "label": "150–175%", "symbol": {"type": "simple-marker", "color": [30, 220, 30, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "175–200%", "label": "175–200%", "symbol": {"type": "simple-marker", "color": [15, 110, 133, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
        {"value": "200+%", "label": "200+%", "symbol": {"type": "simple-marker", "color": [0, 0, 235, 0.9], "size": 16, "outline": {"color": [0, 0, 0, 0.7], "width": 1}}},
    ],
}


class APRFCNRCSSWEMapViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_nrcs_swe_map"

    visualization_group = "Water Supply"
    visualization_label = "APRFC NRCS SWE Map"
    visualization_type = "map"
    visualization_description = (
        "APRFC Alaska NRCS/SNOTEL Snow Water Equivalent map from nrcs_swe.json."
    )
    visualization_tags = ["aprfc", "nrcs", "swe", "snow", "water supply", "map"]
    visualization_attribution = "NOAA / NWS / APRFC / NRCS"

    visualization_args = {
        "product": get_swe_product_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, product="swe", metadata=None, **kwargs):
        from rfc_plugins.water_supply import validate_dependencies

        validate_dependencies()
        self.product = product
        super().__init__(metadata=metadata)

    def read(self):
        swe_geojson = fetch_aprfc_nrcs_swe_geojson(product=self.product)

        renderer = (
            SWE_PERCENT_RENDERER
            if self.product == "percent_normal"
            else SWE_RENDERER
        )

        layer_name = (
            "APRFC NRCS SWE % Normal"
            if self.product == "percent_normal"
            else "APRFC NRCS SWE"
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
                            "name": layer_name,
                            "popup": {
                                "title": "{name}",
                                "content": (
                                    "<b>Station ID:</b> {lid}<br>"
                                    "<b>Elevation:</b> {elev} ft<br>"
                                    "<b>Date:</b> {date}<br>"
                                    "<b>SWE:</b> {swe} in<br>"
                                    "<b>SWE % Normal:</b> {pct}%<br>"
                                    "<b>Average SWE:</b> {avg} in"
                                ),
                            },
                            "renderer": renderer,
                            "labelingInfo": [
                                {
                                    "labelExpressionInfo": {
                                        "expression": "$feature.label"
                                    },
                                    "symbol": {
                                        "type": "text",
                                        "color": "black",
                                        "haloColor": "white",
                                        "haloSize": 1.5,
                                        "font": {
                                            "size": 12,
                                            "weight": "bold",
                                        },
                                    },
                                }
                            ],
                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": swe_geojson,
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