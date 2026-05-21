from intake.source import base

from .utilities import (
    get_breakup_river_dropdown,
    build_breakup_boxplot_figure,
)


class APRFCBreakupDatesRiverViewViewer(base.DataSource):
    container = "python"
    version = "0.0.3"
    name = "aprfc_breakup_dates_river_view"

    visualization_group = "Seasonal Interest"
    visualization_label = "Breakup Dates River View"
    visualization_type = "plotly"

    visualization_description = (
        "APRFC historical breakup-date boxplot viewer for the "
        "Kuskokwim and Yukon Rivers."
    )
    visualization_tags = ["aprfc", "seasonal", "breakup", "river", "boxplot"]
    visualization_attribution = "NOAA / NWS / APRFC"

    visualization_args = {
        "river": get_breakup_river_dropdown(),
        "normals_start_year": "text",
        "normals_end_year": "text",
        "year_to_plot": "text",
    }

    loading_icon = False
    _user_parameters = []

    def __init__(
        self,
        river="kuskokwim",
        normals_start_year="1980",
        normals_end_year="2025",
        year_to_plot="2026",
        metadata=None,
        **kwargs,
    ):
        from rfc_plugins.seasonal import validate_dependencies

        validate_dependencies()

        self.river = river
        self.normals_start_year = normals_start_year
        self.normals_end_year = normals_end_year
        self.year_to_plot = year_to_plot

        super().__init__(metadata=metadata)

    def read(self):
        return build_breakup_boxplot_figure(
            river=self.river,
            normals_start_year=self.normals_start_year,
            normals_end_year=self.normals_end_year,
            year_to_plot=self.year_to_plot,
        )