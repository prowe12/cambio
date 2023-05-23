#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 15:49:24 2022

@author: prowe
"""

import numpy as np

from cambio.utils.cambio_utils import sigmafloor


class ClimateState:
    """Climate State Class"""

    def __init__(
        self,
        preindust_c_atm: float,
        preindust_c_ocean: float,
        preindust_albedo: float,
        dtime: float,
        time0: float,
    ) -> None:
        """
        Create an instance of the class
        @param  stochastic_c_atm_std_dev  Std dev of atm. carbon
        """
        # Parameter for stochastic processes (0 for no randomness in c_atm)
        # self.stochastic_c_atm_std_dev: float = stochastic_c_atm_std_dev

        # Fill in read-in values
        self.c_atm: float = preindust_c_atm
        self.c_ocean: float = preindust_c_ocean
        self.albedo: float = preindust_albedo

        # Initialize remaining values with placeholders (values don't mean anything)
        self.temp_anomaly: float = 0
        self.ph: float = 0
        self.temp_c: float = 0
        self.flux_ha: float = 0
        self.flux_ao: float = 0
        self.flux_oa: float = 0
        self.flux_al: float = 0
        self.flux_la: float = 0
        self.year: float = time0 - dtime

    def diagnose_ocean_surface_ph(self, climate_params: dict[str, float]):
        """
        Compute ocean pH as a function of atmospheric CO2
        @param climate_params
        """
        preindust_c_atm = climate_params["preindust_c_atm"]
        preindust_ph = climate_params["preindust_ph"]

        self.ph = -np.log10(self.c_atm / preindust_c_atm) + preindust_ph

    def diagnose_temp_anomaly(self, climate_params: dict[str, float]):
        """
        Compute a temperature anomaly from the atmospheric carbon amount
        @param climate_params
        """
        # climate_params variables used here
        climate_sensitivity = climate_params["climate_sensitivity"]
        preindust_c_atm = climate_params["preindust_c_atm"]

        self.temp_anomaly = climate_sensitivity * (self.c_atm - preindust_c_atm)

    def diagnose_flux_atm_ocean(self, climate_params: dict[str, float]):
        """
        Compute flux of carbon from the atmosphere to the ocean
        @param climate_params
        """
        self.flux_ao = climate_params["k_ao"] * self.c_atm

    def diagnose_flux_ocean_atm(self, climate_params: dict[str, float]):
        """
        Compute temperature-dependent degassing flux of carbon from ocean to atmosphere
        @param c_ocean
        @param temp_anomaly
        """
        k_oa = climate_params["k_oa"]
        ocean_degas_ff = climate_params["ocean_degas_flux_feedback"]
        self.flux_oa = k_oa * (1 + ocean_degas_ff * self.temp_anomaly) * self.c_ocean

    def diagnose_flux_atm_land(self, climate_params: dict[str, float]):
        """
        Compute the terrestrial carbon sink: flux from atmosphere to land
        @param climate_params
        """
        # Variables from climate_params used here
        k_al0 = climate_params["k_al0"]
        k_al1 = climate_params["k_al1"]
        temp_anomaly_feedback = climate_params["temp_anomaly_feedback"]
        flux_al_trans_temp_interval = climate_params["flux_al_transition_temp_interval"]
        flux_al_transition_temp = climate_params["flux_al_transition_temp"]
        fractional_flux_al_floor = climate_params["fractional_flux_al_floor"]

        if temp_anomaly_feedback:
            temp_anomaly: float = self.temp_anomaly
        else:
            temp_anomaly: float = 0

        sigma_floor_val = sigmafloor(
            temp_anomaly,
            flux_al_transition_temp,
            flux_al_trans_temp_interval,
            fractional_flux_al_floor,
        )

        self.flux_al = k_al0 + k_al1 * sigma_floor_val * self.c_atm

    def diagnose_flux_land_atm(self, climate_params: dict[str, float]):
        """
        Compute the terrestrial carbon source: flux from land to atm
        @param climate_params
        """
        self.flux_la = climate_params["k_la"]

    def diagnose_albedo_w_constraint(
        self,
        climate_params: dict[str, float],
    ):
        """
        Compute the albedo as a function of temperature, constrained so the
        change can't exceed a certain amount per year, if so flagged
        @param climate_params
        """
        dtime = climate_params["dtime"]
        trans_temp = climate_params["albedo_transition_temp"]

        if climate_params["albedo_with_no_constraint"]:
            prev_albedo: float = self.albedo
        else:
            prev_albedo: float = 0
            dtime = 0

        # Find the albedo without constraint
        albedo: float = self.diagnose_albedo(trans_temp, climate_params)

        # Applying a constraint, if called for
        if (prev_albedo != 0) & (dtime != 0):
            albedo_change = albedo - prev_albedo
            max_albedo_change = climate_params["max_albedo_change_rate"] * dtime
            if np.abs(albedo_change) > max_albedo_change:
                this_albedo_change = np.sign(albedo_change) * max_albedo_change
                albedo = prev_albedo + this_albedo_change

        self.albedo = albedo

    def diagnose_albedo(
        self, trans_temp: float, climate_params: dict[str, float]
    ) -> float:
        """
        Return the albedo as a function of temperature anomaly
        @param trans_temp
        @returns albedo
        """
        # trans_temp was previously ClimateParams.albedo_transition_temperature
        interval = climate_params["albedo_transition_interval"]
        floor = climate_params["fractional_albedo_floor"]
        preind_albedo = climate_params["preindust_albedo"]
        albedo = (
            sigmafloor(self.temp_anomaly, trans_temp, interval, floor) * preind_albedo
        )

        self.albedo = albedo
        return albedo

    def diagnose_delta_t_from_albedo(self, climate_params: dict[str, float]):
        """
        Compute additional planetary temperature increase resulting
        from a lower albedo and add it to temp_anomaly. Based on the
        idea of radiative balance, ASR = OLR
        @param climate_params
        """
        preindust_albedo = climate_params["preindust_albedo"]
        dtemp = (self.albedo - preindust_albedo) * climate_params["albedo_sensitivity"]
        self.temp_anomaly += dtemp

    def diagnose_stochastic_c_atm(self, climate_params: dict[str, float]):
        """
        Compute noisy version of the atmospheric carbon amt (randomized based on std dev)
        @param climate_params
        """
        stochastic_c_atm_std_dev = climate_params["stochastic_c_atm_std_dev"]

        self.c_atm = np.random.normal(self.c_atm, stochastic_c_atm_std_dev)

    def update_c_atm(self, dtime: float):
        """
        Update the carbon in the atmosphere based on all the fluxes
        """
        self.c_atm += (
            self.flux_la + self.flux_oa - self.flux_ao - self.flux_al + self.flux_ha
        ) * dtime

    def update_c_ocean(self, dtime: float):
        """
        Update the carbon in the ocean based on all the fluxes
        """
        self.c_ocean += (self.flux_ao - self.flux_oa) * dtime

    def update_flux_ha(self, flux_human_atm: float):
        self.flux_ha = flux_human_atm

    def diagnose_actual_temperature(self):
        """
        Compute degrees C from a temperature anomaly
        @returns temperature in Celsius
        """
        self.temp_c = self.temp_anomaly + 14

    def update_year(self, dtime: float):
        """
        Update the year
        dtime  The time step, in years
        """
        self.year += dtime
