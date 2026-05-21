from intake.source import base


BASE_URL = "https://www.weather.gov/images/aprfc/qpf-qpe-maps"


PRODUCT_OPTIONS = {
    "precip": "Accumulated QPE / QPF",
    "return_frequency": "Accumulated Return Frequency",
}


DAY_OPTIONS = {
    "10DayQPE": "QPE -10 Day",
    "7DayQPE": "QPE -7 Day",
    "4DayQPE": "QPE -4 Day",
    "3DayQPE": "QPE -3 Day",
    "2DayQPE": "QPE -2 Day",
    "1DayQPE": "QPE -1 Day",

    "qpf-1Day": "QPF 1 Day",
    "qpf-2Day": "QPF 2 Day",
    "qpf-3Day": "QPF 3 Day",
    "qpf-4Day": "QPF 4 Day",
    "qpf-7Day": "QPF 7 Day",
    "qpf-10Day": "QPF 10 Day",
}


RETURN_FREQ_OPTIONS = {
    "retrat_10DayQPE": "Return Frequency QPE -10 Day",
    "retrat_7DayQPE": "Return Frequency QPE -7 Day",
    "retrat_4DayQPE": "Return Frequency QPE -4 Day",
    "retrat_3DayQPE": "Return Frequency QPE -3 Day",
    "retrat_2DayQPE": "Return Frequency QPE -2 Day",
    "retrat_1DayQPE": "Return Frequency QPE -1 Day",

    "retrat_1DayQPF": "Return Frequency QPF 1 Day",
    "retrat_2DayQPF": "Return Frequency QPF 2 Day",
    "retrat_3DayQPF": "Return Frequency QPF 3 Day",
    "retrat_4DayQPF": "Return Frequency QPF 4 Day",
    "retrat_7DayQPF": "Return Frequency QPF 7 Day",
    "retrat_10DayQPF": "Return Frequency QPF 10 Day",
}


def get_product_dropdown():
    return [
        {"label": label, "value": key}
        for key, label in PRODUCT_OPTIONS.items()
    ]


def get_day_dropdown():
    options = []

    for key, label in DAY_OPTIONS.items():
        options.append({"label": label, "value": key})

    return options


def get_return_frequency_dropdown():
    options = []

    for key, label in RETURN_FREQ_OPTIONS.items():
        options.append({"label": label, "value": key})

    return options


class APRFCAccumQPEQPFImagesViewer(base.DataSource):
    container = "python"
    version = "0.0.3"
    name = "aprfc_accum_qpe_qpf_images"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "Accumulated QPE/QPF"
    visualization_type = "image"

    visualization_description = (
        "APRFC accumulated QPE/QPF and return frequency images."
    )

    visualization_tags = [
        "aprfc",
        "qpe",
        "qpf",
        "precipitation",
        "return frequency",
        "image",
    ]

    visualization_attribution = "NOAA / NWS / APRFC"

    visualization_args = {
        "product": get_product_dropdown(),
        "day": get_day_dropdown(),
    }

    loading_icon = False
    _user_parameters = []

    def __init__(
        self,
        product="precip",
        day="qpf-1Day",
        metadata=None,
        **kwargs,
    ):
        from rfc_plugins.weather import validate_dependencies

        validate_dependencies()

        self.product = product
        self.day = day

        super().__init__(metadata=metadata)

    def read(self):

        if self.product == "precip":
            image_name = f"{self.day}.png"

        elif self.product == "return_frequency":

            if self.day.startswith("qpf-"):
                suffix = self.day.replace("qpf-", "")
                image_name = f"retrat_{suffix}QPF.png"

            else:
                image_name = f"retrat_{self.day}.png"

        else:
            raise ValueError(f"Unknown product: {self.product}")

        image_url = f"{BASE_URL}/{image_name}"

        print(
            f"[APRFCAccumQPEQPFImagesViewer] "
            f"Resolved image URL: {image_url}"
        )

        return image_url