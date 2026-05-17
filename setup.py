from setuptools import setup, find_packages

INSTALL_REQUIRES = [
    "intake==2.0.7",
    "requests",
]

setup(
    name="RFC_plugins",
    version="0.0.1",
    description="RFC plugins for TethysDash",
    author="Iman Maghami",
    packages=find_packages(),
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    entry_points={
        "intake.drivers": [
            # River Observations and Forecasts
            "rfc_river_streamflow = river_observations_and_forecasts.river_streamflow:RFCRiverStreamflowViewer",
            # "aprfc_48hr_flood_outlook = river_observations_and_forecasts.flood_outlook_48hr:APRFCFloodOutlook48hrViewer",
            # "aprfc_5day_flood_outlook = river_observations_and_forecasts.flood_outlook_5day:APRFCFloodOutlook5DayViewer",
            # "aprfc_hefs_plots = river_observations_and_forecasts.hefs_plots:APRFCHEFSPlotsViewer",
            # "aprfc_mmefs_plots = river_observations_and_forecasts.mmefs_plots:APRFCMMEFSPlotsViewer",

            # Weather Observations and Forecasts
            "rfc_precip_viewer = weather_observations_and_forecasts.qpe_qpf:RFCPrecipViewer",
            "rfc_ndfd_viewer = weather_observations_and_forecasts.ndfd:RFCNDFDViewer",
            "rfc_mrms_viewer = weather_observations_and_forecasts.mrms:RFCMRMSViewer",
            "rfc_fdd_map = weather_observations_and_forecasts.degree_days_map:RFCFreezingDegreeDaysMap",
            "rfc_fdd_timeseries = weather_observations_and_forecasts.degree_days_timeseries:RFCFreezingDegreeDaysTimeSeries",
            "rfc_tdd_map = weather_observations_and_forecasts.thawing_degree_days_map:RFCThawingDegreeDaysMap",
            "rfc_tdd_timeseries = weather_observations_and_forecasts.thawing_degree_days_timeseries:RFCThawingDegreeDaysTimeSeries",
            # "aprfc_national_precip_analysis = weather_observations_and_forecasts.national_precip_analysis:APRFCNationalPrecipAnalysisViewer",
            # "aprfc_freeze_level_maps = weather_observations_and_forecasts.freeze_level_maps:APRFCFreezeLevelMapsViewer",
            # "aprfc_nbm_snow_level_forecast = weather_observations_and_forecasts.nbm_snow_level_forecast:APRFCNBMSnowLevelForecastViewer",
            # "aprfc_national_snow_data = weather_observations_and_forecasts.national_snow_data:APRFCNationalSnowDataViewer",
            # "rfc_weather_forecasts = weather_observations_and_forecasts.weather_forecasts:RFCWeatherForecastsViewer",
            # "rfc_satellite_viewer = weather_observations_and_forecasts.satellite:RFCSatelliteViewer",
            # "rfc_radar_viewer = weather_observations_and_forecasts.radar:RFCRadarViewer",

            # Water Supply
            # "aprfc_nrcs_swe_data = water_supply.nrcs_swe_data:APRFCNRCSSWEDataViewer",
            # "aprfc_snow_depth = water_supply.snow_depth:APRFCSnowDepthViewer",
            # "aprfc_bradley_lake = water_supply.bradley_lake:APRFCBradleyLakeViewer",

            # Climate and History
            # "aprfc_drought = climate_and_history.drought:APRFCDroughtViewer",
            "rfc_cpc_outlooks = climate_and_history.cpc_outlooks:RFCCPCOutlooksViewer",

            # Seasonal Interest
            # "aprfc_interactive_breakup_map = seasonal_interest.interactive_breakup_map:APRFCInteractiveBreakupMapViewer",
            # "aprfc_breakup_dates_river_view = seasonal_interest.breakup_dates_river_view:APRFCBreakupDatesRiverViewViewer",
            "aprfc_breakup_temperature_outlooks = seasonal_interest.breakup_temperature_outlooks:APRFCBreakupTemperatureOutlooksViewer",
            # "aprfc_water_temperature = seasonal_interest.water_temperature:APRFCWaterTemperatureViewer",
            # "aprfc_ice_thickness = seasonal_interest.ice_thickness:APRFCIceThicknessViewer",

            # Additional Info
            # "aprfc_hawaii_rfc_forecasts = additional_info.hawaii_rfc_forecasts:APRFCHawaiiRFCForecastsViewer",
        ]
    },
    zip_safe=False,
)