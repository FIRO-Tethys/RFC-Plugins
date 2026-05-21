from intake.source import base


MMEFS_BASE_URL = "https://www.weather.gov/images/aprfc/MMEFS"


MMEFS_SITE_OPTIONS = {
    "ABLA2": "Kobuk River at Ambler (ABLA2)",
    "ALLA2": "Koyukuk River at Allakaket (ALLA2)",
    "APTA2": "Anchor River at New Sterling Highway (APTA2)",
    "BTTA2": "Koyukuk River at Bettles (BTTA2)",
    "CHLA2": "Little Chena nr Fairbanks (CHLA2)",
    "CHRA2": "Chester Creek at Arctic Blvd (CHRA2)",
    "CKTA2": "Chilkat River at Klukwan (CKTA2)",
    "COOA2": "Kenai River at Cooper Landing (COOA2)",
    "CRHA2": "Chena River blw Hunts Creek (CRHA2)",
    "CRNA2": "Chisana River at Northway (CRNA2)",
    "CRUA2": "Colville River at Umiat (CRUA2)",
    "ERBA2": "Eagle River at Glenn Highway (ERBA2)",
    "EYAA2": "Eyak River (EYAA2)",
    "FMMA2": "Mosquito Fork Forty Mile (FMMA2)",
    "FMRA2": "Forty Mile Taylor Highway (FMRA2)",
    "FMWA2": "Forty Mile Walker Fork (FMWA2)",
    "GAKA2": "Gakona River (GAKA2)",
    "GPOA2": "Gulkana River at Paxson Lake (GPOA2)",
    "GRSA2": "Gulkana River at Sourdough (GRSA2)",
    "HNRA2": "Nenena River at Healy (HNRA2)",
    "KIAA2": "Kobuk River at Kiana (KIAA2)",
    "KLUA2": "Klutina River (KLUA2)",
    "KNKA2": "Knik River (KNKA2)",
    "KRHA2": "Koyukuk River at Hughes (KRHA2)",
    "KUPA2": "Kuparuk River (KUPA2)",
    "LSHA2": "Little Susitna at Houston (LSHA2)",
    "LSUA2": "Little Susitna Hatcher Pass (LSUA2)",
    "MATA2": "Matanuska River at Palmer (MATA2)",
    "MCDA2": "Chena River at Moose Creek (MCDA2)",
    "MFKA2": "Middle Fork Koyukuk River (MFKA2)",
    "MNDA2": "Mendenhall River (MNDA2)",
    "MPTA2": "Trail River (MPTA2)",
    "NEBA2": "Nebesna River (NEBA2)",
    "NINA2": "Ninilchik River (NINA2)",
    "RESA2": "Resurrection River (RESA2)",
    "SALA2": "Salcha River (SALA2)",
    "SCKA2": "Staney Creek (SCKA2)",
    "SHIA2": "Ship Creek (SHIA2)",
    "SIXA2": "Six Mile River (SIXA2)",
    "SKLA2": "Kenai River at Skilak Lake Outlet (SKLA2)",
    "SKWA2": "Skwentna River (SKWA2)",
    "SLAA2": "Slate Creek (SLAA2)",
    "SNOA2": "Snow River (SNOA2)",
    "SRYA2": "Situk River (SRYA2)",
    "TAZA2": "Tazlina River (TAZA2)",
    "TKUA2": "Taku River (TKUA2)",
    "TLNA2": "Tanana River near Tetlin (TLNA2)",
    "TONA2": "Tonsina River (TONA2)",
    "TRAA2": "Tok River (TRAA2)",
    "TRTA2": "Talkeetna River above railroad bridge (TRTA2)",
    "TYAA2": "Taiya River (TYAA2)",
    "UCHA2": "Chena River near Two Rivers (UCHA2)",
    "WILA2": "Willow Creek at Parks Highway (WILA2)",
    "WLWA2": "Willow Creek above Deception Creek (WLWA2)",
    "WULA2": "Wulik River (WULA2)",
    "YLKA2": "Yentna River at Lake Creek (YLKA2)",
    "YSSA2": "Yentna River at Susitna Station (YSSA2)",
}


def get_mmefs_site_dropdown():
    return [
        {"label": label, "value": site_id}
        for site_id, label in MMEFS_SITE_OPTIONS.items()
    ]


class APRFCMMEFSPlotsViewer(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "aprfc_mmefs_plots"

    visualization_group = "River Observations and Forecasts"
    visualization_label = "APRFC MMEFS Plots"
    visualization_type = "image"

    visualization_args = {
        "site": get_mmefs_site_dropdown(),
    }

    visualization_description = (
        "APRFC experimental MMEFS short-range ensemble forecast plots."
    )
    visualization_tags = [
        "aprfc",
        "river",
        "mmefs",
        "ensemble",
        "forecast",
        "image",
    ]
    visualization_attribution = "NOAA / NWS / APRFC"

    loading_icon = False
    _user_parameters = []

    def __init__(self, site="CHLA2", metadata=None, **kwargs):
        from rfc_plugins.river import validate_dependencies

        validate_dependencies()
        self.site = site
        super().__init__(metadata=metadata)

    def read(self):
        image_url = f"{MMEFS_BASE_URL}/{self.site}.shortrange.nbm.png"

        print(
            f"[APRFCMMEFSPlotsViewer] Resolved image URL: {image_url} "
            f"(site={self.site})"
        )

        return image_url