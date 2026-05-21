from intake.source import base


QPE_QPF_BASE_URL = "https://www.weather.gov/images/aprfc/qpf-qpe-maps"


PRODUCT_OPTIONS = {
    "precip": "QPE / QPF",
    "return_frequency": "Return Frequency",
}


DAY_OPTIONS = {
    "-10": "Day -10",
    "-9": "Day -9",
    "-8": "Day -8",
    "-7": "Day -7",
    "-6": "Day -6",
    "-5": "Day -5",
    "-4": "Day -4",
    "-3": "Day -3",
    "-2": "Day -2",
    "-1": "Yesterday",
    "1": "Today",
    "2": "Day 2",
    "3": "Day 3",
    "4": "Day 4",
    "5": "Day 5",
    "6": "Day 6",
    "7": "Day 7",
    "8": "Day 8",
    "9": "Day 9",
    "10": "Day 10",
}


def get_product_dropdown():
    return [
        {"label": label, "value": key}
        for key, label in PRODUCT_OPTIONS.items()
    ]


def get_day_dropdown():
    return [
        {"label": label, "value": key}
        for key, label in DAY_OPTIONS.items()
    ]


class APRFCQPEQPFImagesViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_qpe_qpf_images"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "Daily QPE/QPF and Return Frequencies"
    visualization_type = "image"

    visualization_args = {
        "product": get_product_dropdown(),
        "day": get_day_dropdown(),
    }

    visualization_description = (
        "APRFC daily QPE/QPF and precipitation return-frequency static images."
    )
    visualization_tags = [
        "aprfc",
        "weather",
        "qpe",
        "qpf",
        "precipitation",
        "return frequency",
        "image",
    ]
    visualization_attribution = "NOAA / NWS / APRFC"

    loading_icon = False
    _user_parameters = []

    def __init__(self, product="precip", day="-1", metadata=None, **kwargs):
        from rfc_plugins.weather import validate_dependencies

        validate_dependencies()
        self.product = product
        self.day = str(day)

        super().__init__(metadata=metadata)

    def read(self):
        if self.product == "precip":
            if self.day in [
                "-10", "-9", "-8", "-7", "-6",
                "-5", "-4", "-3", "-2", "-1",
            ]:
                image_name = f"has_qpe{self.day}.png"
            else:
                qpf_hour = int(self.day) * 24
                image_name = f"has_qpf{qpf_hour}.png"

        elif self.product == "return_frequency":
            if self.day in [
                "-10", "-9", "-8", "-7", "-6",
                "-5", "-4", "-3", "-2", "-1",
            ]:
                image_name = f"has_retrat24_{self.day}.png"
            else:
                image_name = f"has_retrat24_{self.day}.png"

        else:
            image_name = "has_qpe-1.png"

        image_url = f"{QPE_QPF_BASE_URL}/{image_name}"

        print(
            f"[APRFCQPEQPFImagesViewer] Resolved image URL: {image_url} "
            f"(product={self.product}, day={self.day})"
        )

        return image_url