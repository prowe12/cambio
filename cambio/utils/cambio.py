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
#
# The pre-industrial climate state is passed in with the inputs.


import numpy as np
from cambio.utils.schemas import CambioInputs


from cambio.utils.cambio_utils import make_emissions_scenario_lte, is_same
from cambio.utils.climate_state import ClimateState
from cambio.utils.cambio_utils import CambioVar


def cambio(climateParams: CambioInputs) -> dict[str, CambioVar]:
    """
    Run the cambio model
    @param climateParams  Required inputs (see notes)
    @returns  The model results
    Notes:
    Inputs must include:
    - start_year  Starting year for the calculation
    - stop_year  Ending year for the calculation
    - dtime = 1.0  time resolution (years)
    - inv_time_constant
    - transition_year = 2040.0  pivot year to start decreasing CO2
    - transition_duration = 20.0  years over which to decrease Co2
    - long_term_emissions = 2.0  ongoing carbon emissions after decarbonization
    - stochastic_c_atm_std_dev  Noise level, in same units as CO2
    - albedo_with_no_constraint = False
    - albedo_feedback = False
    - temp_anomaly_feedback = False
    Outputs include:
    - C_atm  carbon amount in atmosphere, GtC
    - C_ocean  carbon amount in ocean, GtC
    - albedo  Earth's albedo
    - T_anomaly  temperature anomaly, K
    - pH  ocean pH
    - T_C  temperature, deg C
    - F_ha  flux human-atmosphere, GtC/year
    - F_ao  flux atmosphere-ocean, GtC/year
    - F_oa  flux ocean-atmosphere, GtC/year
    - F_la  flux land-atmosphere, GtC/year
    - F_al  flux atmosphere-land, GtC/year
    - year
    """
    # TODO: fix the above docstring
    # TODO: output units

    # Call the LTE emissions scenario maker with these parameters
    # time is in years
    # flux_human_atm is in GtC/year
    # TODO: output units
    time, flux_human_atm = make_emissions_scenario_lte(
        climateParams.start_year,
        climateParams.stop_year,
        climateParams.dtime,
        climateParams.inv_time_constant,
        climateParams.transition_year,
        climateParams.transition_duration,
        climateParams.long_term_emissions,
    )

    climateState = ClimateState(
        climateParams.preindust_c_atm,
        climateParams.preindust_c_ocean,
        climateParams.preindust_albedo,
        climateParams.dtime,
        time[0],
    )
    climate_state_vars = vars(climateState).keys()

    # Initialize the dictionary that will hold the time series
    # In the Jupyter notebook code, climate is a list of dictionaries,
    # one dictionary per time steps.  Here it is a dictionary of np arrays,
    # initialized to zero
    ntimes = len(time)
    climate: dict[str, CambioVar] = {}
    for key in climate_state_vars:  # climatestate:
        climate[key] = np.zeros(ntimes)

    # Propagate through time: loop over all times in scheduled flow
    for i in range(ntimes):
        # Update the human-to-atmosphere
        climateState.update_flux_ha(flux_human_atm[i])

        # Propagate
        climateState = propagate_climate_state(climateState, climateParams)

        # Append to climate variables
        for key in climate_state_vars:
            climate[key][i] = getattr(climateState, key)

    # Add variables that are constants
    # TODO: why is this a numpy array of length 1? Who uses this?)
    # climate["albedo_trans_temp"] = np.array([climateParams.albedo_transition_temp])
    # climate["flux_al_trans_temp"] = np.array([climateParams.flux_al_transition_temp])

    # TODO: do we need to do this here?  Why not in the test suite?
    # QC: make sure the input and output times and human co2 emissions are same
    if not is_same(time, climate["year"]):
        raise ValueError("The input and output times differ!")
    if not is_same(flux_human_atm, climate["flux_ha"]):
        raise ValueError("The input and output anthropogenic emissions differ!")

    return climate


def propagate_climate_state(
    climateState: ClimateState, climateParams: CambioInputs
) -> ClimateState:
    """
    Propagate the state of the climate, with a specified anthropogenic
    carbon flux
    @param climateState  The current state of the climate, which is modified here
    @param climateParams  Climate Parameters (constants that should never be modified!)
    @returns The updated climate state
    """

    climate_params = climateParams.dict()

    # Only turn on noise if the noise level is > 0
    stochastic_c_atm = bool(climate_params["stochastic_c_atm_std_dev"] > 0)

    # Get the temperature anomaly resulting from carbon concentrations
    climateState.diagnose_temp_anomaly(climate_params)

    # Get fluxes, optionally activating the impact temperature has on land
    # (via photosynthesis reduction)
    # TODO: make sure diagnose_flux_oa has if/else as for f_al
    climateState.diagnose_flux_ocean_atm(climate_params)
    climateState.diagnose_flux_atm_land(climate_params)

    # Get other fluxes resulting from carbon concentrations
    climateState.diagnose_flux_atm_ocean(climate_params)
    climateState.diagnose_flux_land_atm(climate_params)

    # Update concentrations of carbon based on these fluxes
    climateState.update_c_atm(climate_params["dtime"])
    climateState.update_c_ocean(climate_params["dtime"])

    # If albedo feedback is turned on, get albedo from temperature anomaly
    # (optionally activating a constraint in case it's changing too fast)
    # Otherwise keep it constant
    if climate_params["albedo_feedback"]:
        climateState.diagnose_albedo_w_constraint(climate_params)
        # Get a new temperature anomaly as impacted by albedo
        climateState.diagnose_delta_t_from_albedo(climate_params)

    # Add stochasticity (random noise) to atmospheric carbon amount, if indicated
    # TODO: this is not tested
    if stochastic_c_atm:
        climateState.diagnose_stochastic_c_atm(climate_params)

    # Ordinary diagnostics
    climateState.diagnose_ocean_surface_ph(climate_params)
    climateState.diagnose_actual_temperature()
    climateState.update_year(climate_params["dtime"])

    # Return the new climate state
    return climateState
