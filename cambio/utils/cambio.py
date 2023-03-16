"""
Code and algorithms written by Steven Neshyba
Refactored for wep app By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

"""
#!/usr/bin/env python
# coding: utf-8

# # Cambio 3.1
#
# ## Cambio 3 equations of motion
# The equations of motion for Cambio3 are as follows:
#
# $$
# F_{land->atm} =  k_{la} \ \ \ (1)
# $$
#
# $$
# F_{atm->land} = k_{al0} +  k_{al1} \times \sigma_{floor}(T_{anomaly})
#                  \times [C_{atm}] \ \ \ (2)
# $$
#
# $$
# F_{ocean->atm} = k_{oa} [C_{ocean}] \ \ \ (3)
# $$
#
# $$
# F_{atm->ocean} = k_{ao} [C_{atm}] \ \ \ (4)
# $$
#
# $$
# F_{human->atm} = \epsilon(t) \ \ \ (5)
# $$
#
#
# ### Significant differences between Cambio2 and Cambio3
#
# One difference is that Cambio3 makes use of a new function that creates
# scheduledflows "on the fly" (instead of picking up a pre-existing file).
# This is the function CL.make_emissions_scenario_lte.
#
# Another difference is that Cambio3 includes feedbacks as well as diagnostics.
# One of these is shown explicitly in Eq. (2) above, where we calculate the
# flux of carbon from the atmosphere to the land. In Cambio2, this was
# just $k_{al0} +  k_{al1} \times [C_{atm}]$, meaning that a
# bigger $k_{al1}$ resulted in a bigger value of the atmosphere-to-land c
# arbon flux. That's called the $CO_2$ fertilization effect -- basically,
# because plants photosynthesize better when there's more $CO_2$ in the air.
# But it's also known that $CO_2$ fertilization suffers diminishing returns
# in a warmer climate. That's where the factor $\sigma_{floor}(T_{anomaly})$
# comes in: if the temperature anomaly rises above some threshold value
# (specified here by 'F_al_transitionT', in the climparams dictionary),
# then $\sigma_{floor}(T_{anomaly})$ drops to some new value, less than $1$,
# which in turn means that $F_{atm->land}$ goes up a little more slowly in
# response to higher $CO_2$ levels in the atmosphere.
#
# ### Using Cambio3.1
# 1. Take snapshots of one some of the results (graphs).
# 2. After modifying flags in propagate_climate_state
# (they start with "I_want ...") to activate a given feedback,
# impact, or constraint of interest, or modifying parameters in the
# climparams dictionary, you'll run the entire notebook again from top to
# bottom, and take more snapshots for comparison.
#
# Goals
# 1. Generate scheduled flows "on the fly," with a specified long term
#    emission value.
# 2. Activate various feedbacks, impacts, and constraints, including:
#    - the impact of temperature on carbon fluxes, and vice versa
#    - the impact of albedo on temperature, and vice versa
#    - stochasticity in the model
#    - constraint on how fast Earth's albedo can change


import numpy as np
from cambio.utils.schemas import CambioInputs


from cambio.utils.cambio_utils import make_emissions_scenario_lte, is_same
from cambio.utils.climate_params import ClimateParams
from cambio.utils.preindustrial_inputs import preindustrial_inputs
from cambio.utils.cambio_utils import diagnose_actual_temperature
from cambio.utils.cambio_utils import CambioVar


def cambio(inputs: CambioInputs) -> tuple[dict[str, CambioVar], dict[str, float]]:
    # TODO: improve this docstring
    """
    Run the cambio model

    @param start_year  Starting year for the calculation
    @param stop_year  Ending year for the calculation
    @param dtime = 1.0  time resolution (years)
    @param inv_time_constant
    @param transition_year = 2040.0  pivot year to start decreasing CO2
    @param transition_duration = 20.0  years over which to decrease co2
    @param long_term_emissions = 2.0  ongoing carbon emissions after decarbonization
    @param For feedbacks and stochastic runs
    @param stochastic_c_atm_std_dev
    @param albedo_with_no_constraint = False
    @param albedo_feedback = False
    @param stochastic_c_atm = False
    @param temp_anomaly_feedback = False
    """

    # Units of variables output by climate model:
    # C_atm and C_ocean: GtC, I think
    # T_anomaly: K
    # f_al, f_la, f_ao, f_oa, f_ha: GtC/year

    # Call the LTE emissions scenario maker with these parameters
    # time is in years
    # flux_human_atm is in GtC/year
    # would be good to output units
    time, flux_human_atm = make_emissions_scenario_lte(
        inputs.start_year,
        inputs.stop_year,
        inputs.dtime,
        inputs.inv_time_constant,
        inputs.transition_year,
        inputs.transition_duration,
        inputs.long_term_emissions,
    )

    # ### Creating a preindustrial Climate State
    # containing the climate state containing preindustrial parameters.
    # We've set the starting year to what was specified above when you
    # created your scenario.
    climate_params = preindustrial_inputs()
    climateParams = ClimateParams(inputs.stochastic_c_atm_std_dev)

    # Propagating through time

    # Make the starting state the preindustrial
    # Create an empty climate state
    climatestate: dict[str, float] = {}
    # Fill in some default (preindustrial) values
    climatestate["C_atm"] = climate_params["preindust_c_atm"]
    climatestate["C_ocean"] = climate_params["preindust_c_ocean"]
    climatestate["albedo"] = climate_params["preindust_albedo"]
    climatestate["T_anomaly"] = 0
    # These are just placeholders (values don't mean anything)
    climatestate["pH"] = 0
    climatestate["T_C"] = 0
    climatestate["F_ha"] = 0
    climatestate["F_ao"] = 0
    climatestate["F_oa"] = 0
    climatestate["F_al"] = 0
    climatestate["F_la"] = 0
    climatestate["year"] = time[0] - inputs.dtime

    # Initialize the dictionary that will hold the time series
    ntimes = len(time)
    climate: dict[str, CambioVar] = {}
    for key in climatestate:
        climate[key] = np.zeros(ntimes)

    # Loop over all the times in the scheduled flow
    for i in range(len(time)):

        # Propagate
        climatestate = propagate_climate_state(
            climatestate,
            climateParams,
            inputs.dtime,
            flux_human_atm[i],
            inputs.albedo_with_no_constraint,
            inputs.albedo_feedback,
            inputs.stochastic_C_atm,
            inputs.temp_anomaly_feedback,
        )

        # Append to climate variables
        for key, value in climatestate.items():
            climate[key][i] = value

    # QC: make sure the input and output times and human co2 emissions are same
    if not is_same(time, climate["year"]):
        raise ValueError("The input and output times differ!")
    if not is_same(flux_human_atm, climate["F_ha"]):
        raise ValueError("The input and output anthropogenic emissions differ!")

    return climate, climate_params


def propagate_climate_state(
    prev_climatestate: dict[str, float],
    climateParams: ClimateParams,
    dtime: float = 1,
    f_ha: float = 0,
    albedo_with_no_constraint: bool = False,
    albedo_feedback: bool = False,
    stochastic_c_atm: bool = False,
    temp_anomaly_feedback: bool = False,
) -> dict[str, float]:
    """
    Propagate the state of the climate, with a specified anthropogenic
    carbon flux

    @param prev_climatestate
    @param ClimateParams  Climate params class
    @param climparams, dtime, F_ha
    @returns dictionary of climate state

    Default anthropogenic carbon flux is zero
    Default time step is 1 year
    Returns a new climate state
    """

    # More inputs (for feedbacks and etc)

    # Extract concentrations from the previous climate state
    c_atm = prev_climatestate["C_atm"]
    c_ocean = prev_climatestate["C_ocean"]

    # Get the temperature anomaly resulting from carbon concentrations
    t_anom = climateParams.diagnose_temp_anomaly(c_atm)

    # Get fluxes (optionally activating the impact temperature has on them)
    if temp_anomaly_feedback:
        f_oa = climateParams.diagnose_flux_ocean_atm(c_ocean, t_anom)
        f_al = climateParams.diagnose_flux_atm_land(t_anom, c_atm)
    else:
        f_oa = climateParams.diagnose_flux_ocean_atm(c_ocean, 0)
        f_al = climateParams.diagnose_flux_atm_land(0, c_atm)

    # Get other fluxes resulting from carbon concentrations
    f_ao = climateParams.diagnose_flux_atm_ocean(c_atm)
    f_la = climateParams.diagnose_flux_land_atm()

    # Update concentrations of carbon based on these fluxes
    c_atm += (f_la + f_oa - f_ao - f_al + f_ha) * dtime
    c_ocean += (f_ao - f_oa) * dtime

    # Get albedo from temperature anomaly (optionally activating a
    # constraint in case it's changing too fast)
    if albedo_with_no_constraint:
        albedo = climateParams.diagnose_albedo_w_constraint(
            t_anom, prev_climatestate["albedo"], dtime
        )
    else:
        albedo = climateParams.diagnose_albedo_w_constraint(t_anom)

    # Get a new temperature anomaly as impacted by albedo (if we want it)
    if albedo_feedback:
        t_anom += climateParams.diagnose_delta_t_from_albedo(albedo)

    # Stochasticity in the model (if we want it)
    if stochastic_c_atm:
        c_atm = climateParams.diagnose_stochastic_c_atm(c_atm)

    # Ordinary diagnostics
    ph_ = climateParams.diagnose_ocean_surface_ph(c_atm)
    temp_c = diagnose_actual_temperature(t_anom)

    # Create a new climate state with these updates
    climatestate: dict[str, float] = {}
    climatestate["C_atm"] = c_atm
    climatestate["C_ocean"] = c_ocean
    climatestate["albedo"] = albedo
    climatestate["T_anomaly"] = t_anom
    climatestate["pH"] = ph_
    climatestate["T_C"] = temp_c
    climatestate["F_ha"] = f_ha
    climatestate["F_ao"] = f_ao
    climatestate["F_oa"] = f_oa
    climatestate["F_la"] = f_la
    climatestate["F_al"] = f_al
    climatestate["year"] = prev_climatestate["year"] + dtime

    # Return the new climate state
    return climatestate
