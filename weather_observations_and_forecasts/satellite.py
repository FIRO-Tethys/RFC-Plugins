# from intake.source import base
# from .utilities import (
#     RFC_OPTIONS,
#     GOES_BAND_OPTIONS,
#     GOES_LOOP_OPTIONS,
#     build_goes_image_url,
# )


# class RFCSatelliteViewer(base.DataSource):
#     container = "python"
#     version = "0.0.1"
#     name = "rfc_satellite_viewer"

#     visualization_group = "Weather Observations and Forecasts"
#     visualization_label = "Satellite"
#     visualization_type = "image"
#     visualization_description = "GOES satellite viewer for RFC-related products."
#     visualization_tags = ["rfc", "weather", "satellite", "goes", "noaa"]
#     visualization_attribution = "NOAA / NESDIS / STAR"

#     visualization_args = {
#         "rfc": "select",
#         "band": "select",
#         "loop": "select",
#     }

#     def __init__(self, rfc="APRFC", band="13", loop="12", metadata=None):
#         self.rfc = rfc
#         self.band = band
#         self.loop = loop
#         super().__init__(metadata=metadata)

#     def read(self):
#         """
#         TethysDash image visualization expects a direct image URL string.
#         """
#         image_url = build_goes_image_url(
#             rfc=self.rfc,
#             band=self.band,
#             loop=self.loop,
#         )

#         print(f"[RFCSatelliteViewer] Resolved image URL: {image_url}")
#         return image_url

from intake.source import base
from .utilities import (
    get_rfc_dropdown,
    get_product_dropdown,
    get_frame_dropdown,
    build_goes_image_url,
)


class RFCSatelliteViewer(base.DataSource):
    container = "python"
    version = "0.0.4"
    name = "rfc_satellite_viewer"

    visualization_group = "Weather Observations and Forecasts"
    visualization_label = "Satellite"
    visualization_type = "image"
    visualization_args = {
        "rfc": get_rfc_dropdown(),
        "product": get_product_dropdown(),
        "frame_back": get_frame_dropdown(),
    }
    visualization_description = "GOES satellite viewer for RFC-related products."
    visualization_tags = ["rfc", "weather", "satellite", "goes", "noaa"]
    visualization_attribution = "NOAA / NESDIS / STAR"
    _user_parameters = []

    loading_icon = False

    def __init__(self, rfc, product, frame_back="0", metadata=None, **kwargs):
        self.rfc = rfc
        self.product = product
        self.frame_back = int(frame_back)
        super(RFCSatelliteViewer, self).__init__(metadata=metadata)

    def read(self):
        image_url = build_goes_image_url(
            rfc=self.rfc,
            product=self.product,
            frame_back=self.frame_back,
        )
        print(
            f"[RFCSatelliteViewer] Resolved image URL: {image_url} "
            f"(frame_back={self.frame_back})"
        )
        return image_url