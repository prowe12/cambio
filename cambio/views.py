"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

Based on Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

import json

from typing import Any
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
import numpy as np

# from plotly.offline import plot
# from plotly.graph_objs import Scatter
# from numpy.typing import NDArray

# from cambio.utils.cambio import cambio
# from cambio.utils.cambio_utils import celsius_to_f, celsius_to_kelvin
from cambio.utils.view_utils import (
    parse_inputs,
    run_model_for_dict,
    make_plots,
)


def get_scenarios_to_plot(request: HttpRequest) -> list[int]:
    """
    Get the scenario ids to plot
    @params request  The HttpRequest
    @returns The scenario ids to plot
    """
    max_scen = 100
    scenario_ids = [
        i
        for i in range(max_scen)
        if request.GET.get(f"plot_scenario{i}", None) is not None
    ]
    return scenario_ids


def get_scenario_units(
    request: HttpRequest,
    unit_defaults: dict[str, str],
    unit_types: dict[str, Any],
) -> dict[str, Any]:
    """
    Get the units from the request
    @params request  The HttpRequest
    @returns The units
    """
    inputs = parse_inputs(request.GET, unit_defaults, unit_types)
    units: dict[str, Any] = {}
    for name, default_unit in unit_defaults.items():
        if name in inputs:
            units[name] = inputs[name]
        else:
            units[name] = default_unit
    return units


def get_scenario_vars(request: HttpRequest, getvars: list[str]) -> dict[str, Any]:
    """
    Get the variables to plot from the request
    @params request  The HttpRequest
    @params getvars  The variables to extract from the request
    """
    inputs = request.GET
    scenario_vars: dict[str, Any] = {}
    for getvar in getvars:
        if getvar in inputs:
            scenario_vars[getvar] = inputs[getvar]
    return scenario_vars


def index(request: HttpRequest) -> HttpResponse:
    """
    Create the view for the main page
    @param request  The HttpRequest
    """

    # # # # # #     Constants    # # # # # # # # # #
    # Default values
    model_run_default_inputs = {
        "id": 0,
        "start_year": 1750.0,  # <!-- start_year"><br> -->
        "stop_year": 2200.0,  # stop_year"><br> -->
        "dtime": 1.0,  # dtime"><br> time resolution (years) -->
        "inv_time_constant": 0.025,  # inv_time_constant"><br> -->
        "transition_year": 2040.0,  # transition_year"><br> # year to start decreasing CO2 -->
        "transition_duration": 20.0,  # transition_duration"><br> years over which to decrease co2  -->
        "long_term_emissions": 2.0,  # long_term_emissions"><br> # ongoing carbon emissions after decarbonization  -->
        "albedo_with_no_constraint": False,  # albedo_with_no_constraint"><br> -->
        "albedo_feedback": False,  # albedo_feedback"><br> -->
        "temp_anomaly_feedback": False,  # temp_anomaly_feedback"><br> -->
        "stochastic_C_atm": False,  # stochastic_C_atm"><br> -->
        "stochastic_c_atm_std_dev": 0.1,  # stochastic_c_atm_std_dev"> <br> -->
    }
    model_run_default_types = {
        "id": int,
        "start_year": float,
        "stop_year": float,
        "dtime": float,
        "inv_time_constant": float,
        "transition_year": float,
        "transition_duration": float,
        "long_term_emissions": float,
        "albedo_with_no_constraint": bool,
        "albedo_feedback": bool,
        "temp_anomaly_feedback": bool,
        "stochastic_C_atm": bool,
        "stochastic_c_atm_std_dev": float,
    }

    # Default values
    unit_defaults = {
        "temp_units": "F",  # temp_units"><br> # F, C, or K -->
        "carbon_units": "GtC",  # c_units"><br> GtC, GtCO2, atm  -->
        "flux_units": "GtC/year",  # flux_type"><br> # total, per year-->
    }
    unit_types = {
        "temp_units": str,
        "carbon_units": str,
        "flux_units": str,
    }

    carbon_vars_to_plot = ["C_atm", "C_ocean"]
    flux_vars_to_plot = ["F_ha", "F_ao", "F_oa", "F_la", "F_al"]
    temp_vars_to_plot = ["T_anomaly", "T_C"]
    vars_to_plot = [
        carbon_vars_to_plot,
        flux_vars_to_plot,
        temp_vars_to_plot,
        [],
        [],
    ]  # , ['pH'], ['albedo']]
    units = [
        [["carbon_units", "GtC"], ["carbon_units", "atm"]],
        [["flux_units", "GtC"], ["flux_units", "GtCO2"]],
        [["temp_units", "C"], ["temp_units", "K"], ["temp_units", "F"]],
        [],
        [],
    ]
    # always plotted: "albedo", "pH"
    # # # # # # # # # # # # # # # # # # # # # # #

    # Get variables from request:
    scenarios_to_plot = get_scenarios_to_plot(request)
    scenario_units = get_scenario_units(request, unit_defaults, unit_types)
    carbon_vars = get_scenario_vars(request, carbon_vars_to_plot)
    flux_vars = get_scenario_vars(request, flux_vars_to_plot)
    temp_vars = get_scenario_vars(request, temp_vars_to_plot)

    # Get cambio inputs from cookies
    cookie_scenarios = [json.loads(value) for value in request.COOKIES.values()]
    cookie_scenarios = list(filter(lambda x: isinstance(x, dict), cookie_scenarios))

    # Put in hashmap (no duplicates allowed)
    cookie_scenarios_dict = {}
    for cookie in cookie_scenarios:
        cookie_scenarios_dict[cookie["id"]] = cookie

    # scenario_inputs = [
    #     parse_cambio_inputs_for_cookies(scenario) for scenario in cookie_scenarios
    # ]
    scenario_inputs_dict = {}
    for scenario_id, scenario in cookie_scenarios_dict.items():
        scenario_inputs_dict[scenario_id] = parse_inputs(
            scenario, model_run_default_inputs, model_run_default_types
        )

    # Get new scenario from get parameters for model run and for saving to cookies
    # *only* if it exists
    new_cookie = False
    new_id = []
    if "id" in request.GET:
        inputs = parse_inputs(
            request.GET, model_run_default_inputs, model_run_default_types
        )
        new_hash = str(hash(json.dumps(inputs)))
        # if new_hash not in request.COOKIES.keys():
        #    scenario_inputs.append(inputs)
        if new_hash not in request.COOKIES.keys():
            scenario_inputs_dict[inputs["id"]] = inputs
            new_cookie = True
            new_id = inputs["id"]

    # Run the model on old and new inputs to get the climate model results
    # (Packed into "scenarios")
    # scenarios = run_model(scenario_inputs, request)
    scenarios = run_model_for_dict(scenario_inputs_dict)

    plot_divs, _ = make_plots(
        [scenarios[i] for i in scenarios_to_plot],
        scenario_units,
        list(carbon_vars.keys()),
        list(flux_vars.keys()),
        list(temp_vars.keys()),
    )
    plot_div_stuff = [
        [var_to_plot, plot_div, unit]
        for var_to_plot, plot_div, unit in zip(vars_to_plot, plot_divs, units)
    ]

    scenario_ids = list(scenarios.keys())
    if len(scenario_ids) <= 0:
        scenario_ids = []
    elif len(scenario_ids) == 1:
        pass
    else:
        scenario_ids = np.sort(scenario_ids)

    plot_scenarios = ["plot_scenario" + str(id) for id in scenario_ids]

    # Variables to pass to html
    context = {
        "plot_divs": plot_div_stuff,
        "vars_to_plot": vars_to_plot,
        "old_scenario_inputs": scenario_inputs_dict,
        "scenarios": scenario_ids,
        "plot_scenarios": plot_scenarios,
        "inputs": model_run_default_inputs,
    }
    # "old_scenario_inputs": enumerate(scenario_inputs),
    response = render(request, "cambio/index.html", context)

    # If there is a new scenario in the get parameters, save it to cookies
    if new_cookie:
        scenario = json.dumps(scenario_inputs_dict[new_id])
        scenario_hash = str(hash(scenario))
        # don't add the new scenario to cookies if it already exists
        # (should not be necessary)
        if scenario_hash not in request.COOKIES.keys():
            response.set_cookie(scenario_hash, scenario)

    return response


# Names for displaying climate variables
# climvar_names = {
#                  'f_ha': 'CO2 flux from humans (GTC)',
#                  'atmos_co2': 'Atmospheric CO2 (GTC)',
#                  'ocean_co2': 'Ocean CO2 (GTC)',
#                  'ocean_ph': 'Ocean pH (GTC)',
#                  't_C': 'temperature (C)',
#                  't_F': 'temperature (F)',
#                  't_anomaly': 'temp. anomaly (C)',
#                  'albedo': 'albedo',
#                  'f_oa': 'CO2 flux from ocean (GTC)',
#                  'f_la': 'CO2 flux from land (GTC)',
#                  'tot_ha': 'total CO2 from humans (GTC)',
#                 }
