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
from cambio.utils.cambio_utils import make_emissions_scenario_lte
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
    - c_atm  carbon amount in atmosphere, GtC
    - c_ocean  carbon amount in ocean, GtC
    - albedo  Earth's albedo
    - temp_anomaly  temperature anomaly, K
    - ph  ocean pH
    - temp_c  temperature, deg C
    - flux_ha  flux human-atmosphere, GtC/year
    - flux_ao  flux atmosphere-ocean, GtC/year
    - flux_oa  flux ocean-atmosphere, GtC/year
    - flux_la  flux land-atmosphere, GtC/year
    - flux_al  flux atmosphere-land, GtC/year
    - year
    """
    # TODO: fix the above docstring
    # TODO: output units

    # Call the LTE emissions scenario maker with these parameters
    # [time] = year, [flux_ha] (flux human->atmosphere) = GtC/year
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
    for key in climate_state_vars:
        climate[key] = np.zeros(ntimes)

    # Propagate through time: loop over all times in scheduled flow
    for i, flux_ha in enumerate(flux_human_atm):
        climateState.propagate(climateParams, flux_ha)

        # Append to climate variables
        for key in climate_state_vars:
            climate[key][i] = getattr(climateState, key)

    return climate
