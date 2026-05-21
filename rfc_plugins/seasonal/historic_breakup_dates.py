from intake.source import base

from .utilities import (
    get_breakup_site_dropdown,
    build_breakup_database_figure,
)


class APRFCHistoricBreakupDatesViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_historic_breakup_dates"

    visualization_group = "Seasonal Interest"
    visualization_label = "Historic Breakup Dates"
    visualization_type = "plotly"

    visualization_description = (
        "APRFC historical breakup-date database plot for individual river locations."
    )
    visualization_tags = ["aprfc", "seasonal", "breakup", "historic", "database"]
    visualization_attribution = "NOAA / NWS / APRFC"

    visualization_args = {
        "site_id": get_breakup_site_dropdown(),
        "start_year": "text",
        "end_year": "text",
    }

    loading_icon = False
    _user_parameters = []

    def __init__(
        self,
        site_id="17",
        start_year="1980",
        end_year="2026",
        metadata=None,
        **kwargs,
    ):
        from rfc_plugins.seasonal import validate_dependencies

        validate_dependencies()

        self.site_id = site_id
        self.start_year = start_year
        self.end_year = end_year

        super().__init__(metadata=metadata)

    def read(self):
        return build_breakup_database_figure(
            site_id=self.site_id,
            start_year=self.start_year,
            end_year=self.end_year,
        )