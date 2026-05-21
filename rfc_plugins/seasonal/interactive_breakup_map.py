from intake.source import base

from .utilities import (
    fetch_aprfc_breakup_river_geojson,
    fetch_aprfc_breakup_village_geojson,
    fetch_aprfc_breakup_metadata,
)


RIVER_STATUS_RENDERER = {
    "type": "unique-value",
    "field": "status",
    "defaultSymbol": {
        "type": "simple-line",
        "color": [255, 255, 255, 0.9],
        "width": 4,
    },
    "uniqueValueInfos": [
        {
            "value": "unknown",
            "label": "Unknown",
            "symbol": {
                "type": "simple-line",
                "color": [241, 29, 254, 0.9],
                "width": 4,
            },
        },
        {
            "value": "mostice",
            "label": "Mostly Ice",
            "symbol": {
                "type": "simple-line",
                "color": [255, 255, 255, 0.9],
                "width": 4,
            },
        },
        {
            "value": "someopen",
            "label": "Some Open",
            "symbol": {
                "type": "simple-line",
                "color": [103, 255, 254, 0.9],
                "width": 4,
            },
        },
        {
            "value": "mostopen",
            "label": "Mostly Open",
            "symbol": {
                "type": "simple-line",
                "color": [1, 161, 215, 0.9],
                "width": 4,
            },
        },
        {
            "value": "open",
            "label": "Open",
            "symbol": {
                "type": "simple-line",
                "color": [0, 0, 156, 0.9],
                "width": 4,
            },
        },
    ],
}


VILLAGE_STATUS_RENDERER = {
    "type": "unique-value",
    "field": "village_status",
    "defaultSymbol": {
        "type": "simple-marker",
        "color": [0, 0, 0, 0.95],
        "size": 7,
        "outline": {"color": [0, 255, 0, 1.0], "width": 1.5},
    },
    "uniqueValueInfos": [
        {
            "value": "none",
            "label": "No Warning",
            "symbol": {
                "type": "simple-marker",
                "color": [0, 0, 0, 0.95],
                "size": 7,
                "outline": {"color": [0, 255, 0, 1.0], "width": 1.5},
            },
        },
        {
            "value": "advise",
            "label": "Flood Advisory",
            "symbol": {
                "type": "simple-marker",
                "color": [255, 165, 0, 0.95],
                "size": 10,
                "outline": {"color": [0, 255, 0, 1.0], "width": 1.5},
            },
        },
        {
            "value": "watch",
            "label": "Flood Watch",
            "symbol": {
                "type": "simple-marker",
                "color": [255, 255, 0, 0.95],
                "size": 10,
                "outline": {"color": [0, 255, 0, 1.0], "width": 1.5},
            },
        },
        {
            "value": "warn",
            "label": "Flood Warning",
            "symbol": {
                "type": "simple-marker",
                "color": [255, 0, 0, 0.95],
                "size": 10,
                "outline": {"color": [0, 255, 0, 1.0], "width": 1.5},
            },
        },
    ],
}


class APRFCInteractiveBreakupMapViewer(base.DataSource):
    container = "python"
    version = "0.0.4"
    name = "aprfc_interactive_breakup_map"

    visualization_group = "Seasonal Interest"
    visualization_label = "Interactive Breakup Map"
    visualization_type = "map"
    visualization_description = (
        "APRFC river breakup status map using APRFC riverStat.json and villages.json."
    )
    visualization_tags = ["aprfc", "seasonal", "breakup", "river", "map"]
    visualization_attribution = "NOAA / NWS / APRFC"

    visualization_args = {}

    loading_icon = False
    _user_parameters = []

    def __init__(self, metadata=None, **kwargs):
        from rfc_plugins.seasonal import validate_dependencies

        validate_dependencies()
        super().__init__(metadata=metadata)

    def read(self):
        river_geojson = fetch_aprfc_breakup_river_geojson()
        village_geojson = fetch_aprfc_breakup_village_geojson()
        metadata = fetch_aprfc_breakup_metadata()

        return {
            "baseMap": (
                "https://server.arcgisonline.com/arcgis/rest/services/"
                "NatGeo_World_Map/MapServer"
            ),
            "layers": [
                {
                    "configuration": {
                        "type": "VectorLayer",
                        "props": {
                            "name": "River Status",
                            "legendEnabled": True,
                            "popup": {
                                "title": "{display_name}",
                                "content": (
                                    "<b>River Status:</b> {status_label}<br>"
                                    f"<b>Map Last Update:</b> {metadata['last_update']}"
                                ),
                            },
                            "renderer": RIVER_STATUS_RENDERER,
                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": river_geojson,
                            },
                        },
                    }
                },
                {
                    "configuration": {
                        "type": "VectorLayer",
                        "props": {
                            "name": "Community Status",
                            "legendEnabled": True,
                            "popup": {
                                "title": "{display_name}",
                                "content": (
                                    "<b>Community Status:</b> {village_status_label}<br>"
                                    f"<b>Map Last Update:</b> {metadata['last_update']}"
                                ),
                            },
                            "renderer": VILLAGE_STATUS_RENDERER,
                            "source": {
                                "type": "GeoJSON",
                                "props": {},
                                "geojson": village_geojson,
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