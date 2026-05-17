from intake.source import base
import httpx
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RFCRiverStreamflowViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "rfc_river_streamflow"
    visualization_group = "River Observations and Forecasts"
    visualization_label = "River Streamflow"
    visualization_type = "plotly"
    visualization_description = (
        "Observed and forecasted streamflow/stage for a selected NWPS gauge."
    )
    visualization_tags = [
        "rfc",
        "gauge",
        "streamflow",
        "observed",
        "forecast",
        "plotly",
    ]
    visualization_attribution = "NOAA / NWPS"
    visualization_args = {"gauge_id": "text"}

    def __init__(self, gauge_id, metadata=None):
        from rfc_plugins.river import validate_dependencies
        validate_dependencies()
        self.api_base_url = "https://api.water.noaa.gov/nwps/v1"
        self.gauge_id = gauge_id
        self.data = None
        self.metadata = None
        super().__init__(metadata=metadata)

    def read(self):
        self.data = self.get_gauge_data()
        self.metadata = self.get_gauge_metadata()

        if not self.data:
            return {
                "data": [],
                "layout": {
                    "title": f"Gauge {self.gauge_id}: No data returned",
                },
            }

        traces = self.create_traces()
        flood_data = self.metadata.get("flood", {}) if self.metadata else {}
        shapes, annotations = self.create_flood_events(flood_data)
        secondary_range = self.get_secondary_data_range(self.data)
        layout = self.create_layout(shapes, annotations, secondary_range)

        return {"data": traces, "layout": layout}

    def get_gauge_data(self):
        try:
            with httpx.Client(verify=False, timeout=None) as client:
                r = client.get(f"{self.api_base_url}/gauges/{self.gauge_id}/stageflow")
                if r.status_code != 200:
                    logger.error("Stageflow request failed: %s %s", r.status_code, r.text)
                    return None
                return r.json()
        except Exception as e:
            logger.error("Error fetching stageflow: %s", e)
            return None

    def get_gauge_metadata(self):
        try:
            with httpx.Client(verify=False, timeout=None) as client:
                r = client.get(f"{self.api_base_url}/gauges/{self.gauge_id}")
                if r.status_code != 200:
                    logger.error("Metadata request failed: %s %s", r.status_code, r.text)
                    return {}
                return r.json()
        except Exception as e:
            logger.error("Error fetching metadata: %s", e)
            return {}
  
    def create_traces(self):
        traces = []
        datasets = ["observed", "forecast"]

        for dataset_name in datasets:
            if dataset_name in self.data:
                dataset = self.data[dataset_name]
                data_points = dataset.get("data", [])

                if data_points:
                    times = [d["validTime"] for d in data_points]
                    primary_values = [d.get("primary", None) for d in data_points]
                    secondary_values = [d.get("secondary", None) for d in data_points]

                    hover_text = []
                    for t, p, s in zip(times, primary_values, secondary_values):
                        utc_time = datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")
                        formatted_time = utc_time.strftime("%a %b %d %Y %I:%M %p UTC")

                        text = f"Time: {formatted_time}<br>{dataset.get('primaryUnits', '')}: {p}"
                        if s is not None and s >= 0:
                            text += f"<br>{dataset.get('secondaryUnits', '')}: {s}"

                        hover_text.append(text)

                    trace = {
                        "x": times,
                        "y": primary_values,
                        "mode": "lines",
                        "name": dataset_name.capitalize(),
                        "yaxis": "y1",
                        "hoverinfo": "text",
                        "text": hover_text,
                    }
                    traces.append(trace)

                    trace_fake = {
                        "x": [times[0]],
                        "y": [0],
                        "yaxis": "y2",
                        "visible": False,
                        "showlegend": False,
                        "hoverinfo": "skip",
                    }
                    traces.append(trace_fake)

        return traces
  
    @staticmethod
    def create_flood_events(flood_data):
        shapes = []
        annotations = []

        categories = flood_data.get("categories", {})
        if not categories:
            return shapes, annotations

        category_colors = {
            "action": "orange",
            "minor": "gold",
            "moderate": "red",
            "major": "purple",
        }

        invalid_values = {None, "", -9999, -9999.0, "-9999", "-9999.0"}

        for category, details in categories.items():
            raw_stage = details.get("stage", None)

            if raw_stage in invalid_values:
                continue

            try:
                stage = float(raw_stage)
            except (TypeError, ValueError):
                continue

            shapes.append({
                "type": "line",
                "x0": 0,
                "x1": 1,
                "xref": "paper",
                "y0": stage,
                "y1": stage,
                "yref": "y1",
                "line": {
                    "color": category_colors.get(category.lower(), "black"),
                    "width": 2,
                    "dash": "dash",
                },
            })

            annotations.append({
                "x": 0,
                "y": stage,
                "xref": "paper",
                "yref": "y1",
                "text": f"{stage:g} {flood_data.get('stageUnits', '')} - {category}",
                "showarrow": False,
                "xanchor": "left",
                "yanchor": "bottom",
                "font": {"color": "black", "size": 11},
            })

        return shapes, annotations

    @staticmethod
    def get_secondary_data_range(data):
        secondary_values = []
        for dataset_name in ["observed", "forecast"]:
            if dataset_name in data:
                for d in data[dataset_name].get("data", []):
                    s = d.get("secondary", None)
                    if s is not None:
                        secondary_values.append(s)

        if not secondary_values:
            return (0, 1)

        min_secondary = min(secondary_values)
        max_secondary = max(secondary_values)
        padding = (max_secondary - min_secondary) * 0.1 if max_secondary != min_secondary else 1

        return (min_secondary - padding, max_secondary + padding)

    @staticmethod
    def extract_names_units(dataset, data_type):
        if data_type == "primary":
            return dataset.get("primaryName", ""), dataset.get("primaryUnits", "")
        elif data_type == "secondary":
            return dataset.get("secondaryName", ""), dataset.get("secondaryUnits", "")
        raise ValueError("data_type must be 'primary' or 'secondary'")

    def create_layout(self, shapes, annotations, secondary_range):
        primary_name = "Primary"
        primary_units = ""
        secondary_name = "Secondary"
        secondary_units = ""

        if "observed" in self.data:
            primary_name, primary_units = self.extract_names_units(self.data["observed"], "primary")
            secondary_name, secondary_units = self.extract_names_units(self.data["observed"], "secondary")
        elif "forecast" in self.data:
            primary_name, primary_units = self.extract_names_units(self.data["forecast"], "primary")
            secondary_name, secondary_units = self.extract_names_units(self.data["forecast"], "secondary")

        station_name = self.metadata.get("name", "Unknown Gauge")
        return {
            "title": f"Gauge: {station_name}<br>ID: {self.gauge_id}",
            "xaxis": {"tickformat": "%b %d\n%I %p"},
            "yaxis": {
                "title": f"{primary_name} ({primary_units})".strip(),
                "side": "left",
            },
            "yaxis2": {
                "title": f"{secondary_name} ({secondary_units})".strip(),
                "side": "right",
                "overlaying": "y",
                "showgrid": False,
                "range": secondary_range,
            },
            "legend": {"orientation": "h", "x": 0, "y": -0.2},
            "margin": {"l": 50, "r": 50, "t": 70, "b": 50},
            "hovermode": "x unified",
            "shapes": shapes,
            "annotations": annotations,
        }