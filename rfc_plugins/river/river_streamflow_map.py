# ============================================================
# RFC RIVER STREAMFLOW MAP PLUGIN
# ============================================================
# Product:
#   River Observations and Forecasts -> River Streamflow Map
#
# Source:
#   NOAA / NWS NWPS River Gauge MapServer
#
# Purpose:
#   Show NWPS river gauge map layers in TethysDash.
#
# Note:
#   This uses ImageLayer, not inline GeoJSON, because the full
#   river gauge layer can contain thousands of points and may fail
#   or be slow as a VectorLayer in TethysDash.
# ============================================================

from __future__ import annotations

from intake.source import base


NWPS_RIVER_GAUGE_SERVICE = (
    "https://mapservices.weather.noaa.gov/eventdriven/rest/services/"
    "water/riv_gauges/MapServer"
)


def get_river_gauge_layer_dropdown():
    """
    NWPS river gauge MapServer layers.

    Main useful layers:
      0  = Observed River Stages
      1  = 24 hour forecast
      2  = 48 hour forecast
      3  = 72 hour forecast
      4  = 96 hour forecast
      5  = 120 hour forecast
      6  = 144 hour forecast
      7  = 168 hour forecast
      15 = Full Forecast Period Stages
    """
    return [
        {"label": "Observed River Stages", "value": "0"},
        {"label": "River Stages 24 hour Forecast", "value": "1"},
        {"label": "River Stages 48 hour Forecast", "value": "2"},
        {"label": "River Stages 72 hour Forecast", "value": "3"},
        {"label": "River Stages 96 hour Forecast", "value": "4"},
        {"label": "River Stages 120 hour Forecast", "value": "5"},
        {"label": "River Stages 144 hour Forecast", "value": "6"},
        {"label": "River Stages 168 hour Forecast", "value": "7"},
        {"label": "Full Forecast Period Stages", "value": "15"},
    ]


class RFCRiverStreamflowMapViewer(base.DataSource):
    """
    NWPS river gauge map viewer.

    This is the map companion to:
        rfc_plugins.river.river_streamflow:RFCRiverStreamflowViewer

    The time-series plugin still takes gauge_id manually for now.
    Later, we can connect map-click to pass the clicked gauge ID.
    """

    container = "python"
    version = "0.0.1"
    name = "rfc_river_streamflow_map"

    visualization_group = "River Observations and Forecasts"
    visualization_label = "River Streamflow Map"
    visualization_type = "map"
    visualization_description = (
        "NWPS river gauge map layers for observed and forecast river stages."
    )
    visualization_tags = [
        "rfc",
        "river",
        "streamflow",
        "stage",
        "gauge",
        "nwps",
        "map",
    ]
    visualization_attribution = "NOAA / NWS / NWPS"

    visualization_args = {
        "layer": get_river_gauge_layer_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(self, layer="0", metadata=None, **kwargs):
        from rfc_plugins.river import validate_dependencies

        validate_dependencies()
        self.layer = str(layer)
        super().__init__(metadata=metadata)

    def read(self):
        print(f"[RFCRiverStreamflowMapViewer] layer={self.layer}")

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
                            "name": "NWPS River Gauges",
                            "source": {
                                "type": "ESRI Image and Map Service",
                                "props": {
                                    "url": NWPS_RIVER_GAUGE_SERVICE,
                                    "params": {
                                        "LAYERS": f"show:{self.layer}",
                                    },
                                },
                            },
                        },
                    }
                }
            ],
            "layerControl": True,
            "viewConfig": {
                "center": [-10686671.116154263, 4721671.572580108],
                "zoom": 4.5,
            },
        }