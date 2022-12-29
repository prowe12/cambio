"""
By Penny Rowe and Daniel Neshyba
2022/12/21

Based on Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

import json

from typing import Any
from django.shortcuts import render
from plotly.offline import plot
from plotly.graph_objs import Scatter
from django.http import HttpRequest, HttpResponse, QueryDict
from numpy.typing import NDArray

from cambio.utils.cambio import cambio
from cambio.utils.cambio_utils import celsius_to_f, celsius_to_kelvin


def getcolor(i: int) -> str:
    """
    Return a a color
    @returns  A string representing a color
    """
    colors = [
        "red",
        "orange",
        "green",
        "cyan",
        "blue",
        "magenta",
        "black",
        "gray",
        "cornflowerblue",
        "olive",
        "tomato",
        "rosybrown",
        "cadetblue",
        "orchid",
        "purple",
    ]
    j = i % len(colors)
    return colors[j]


def get_scenario_units(request: HttpRequest) -> dict[str, Any]:
    """
    Get the units from the request
    """
    inputs = parse_cambio_inputs_for_units(request.GET)
    units: dict[str, Any] = {}
    units["carbon_units"] = inputs["carbon_units"]
    units["flux_units"] = inputs["flux_units"]
    units["temp_units"] = inputs["temp_units"]
    return units


def get_scenario_vars(request: HttpRequest, getvars: list[str]) -> dict[str, Any]:
    """
    Get the variables to plot from the request
    @params request  The HttpRequest
    @params getvars  The variables to extract from the request
    """
    inputs = request.GET  # parse_cambio_inputs(request.GET)
    scenario_vars: dict[str, Any] = {}
    for getvar in getvars:
        if getvar in inputs:
            scenario_vars[getvar] = inputs[getvar]
    return scenario_vars


def parse_cambio_inputs_for_cookies(input_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Parse the inputs
    @param input_dict  A hashmap of the input variable names and their values as strings
    @returns  A hashmap of the input variable names and their values as the proper type
    """

    # Default values
    inputs = {
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
    varnames = {
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

    for varname, vartype in varnames.items():
        if varname not in input_dict:
            continue

        valstr = input_dict[varname]
        if valstr == "":
            continue

        # TODO: this might make us vulnerable to injection code
        try:
            inputs[varname] = vartype(valstr)
        except ValueError:
            print(f"Error converting value {varname}={valstr} to {vartype}")
    return inputs


def parse_cambio_inputs(input_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Parse the inputs
    @param input_dict  A hashmap of the input variable names and their values as strings
    @returns  A hashmap of the input variable names and their values as the proper type
    """

    # Default values
    inputs = {
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
        "temp_units": "F",  # temp_units"><br> # F, C, or K -->
        "c_units": "GtC",  # c_units"><br> GtC, GtCO2, atm  -->
        "flux_type": "/year",  # flux_type"><br> # total, per year-->
        "plot_flux_diffs": True,  # plot_flux_diffs"><br> -->
    }
    varnames = {
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
        "temp_units": str,
        "c_units": str,
        "flux_type": str,
        "plot_flux_diffs": bool,
    }

    for varname, vartype in varnames.items():
        if varname not in input_dict:
            continue

        valstr = input_dict[varname]
        if valstr == "":
            continue

        # TODO: this might make us vulnerable to injection code
        try:
            inputs[varname] = vartype(valstr)
        except ValueError:
            print(f"Error converting value {varname}={valstr} to {vartype}")
    return inputs


def parse_cambio_inputs_for_units(input_dict: QueryDict) -> dict[str, Any]:
    """
    Parse the inputs
    @param input_dict  A hashmap of the input variable names and their values as strings
    @returns  A hashmap of the input variable names and their values as the proper type
    """

    # Default values
    inputs = {
        "temp_units": "F",  # temp_units"><br> # F, C, or K -->
        "carbon_units": "GtC",  # c_units"><br> GtC, GtCO2, atm  -->
        "flux_units": "GtC/year",  # flux_type"><br> # total, per year-->
    }
    varnames = {
        "temp_units": str,
        "carbon_units": str,
        "flux_units": str,
    }

    for varname, vartype in varnames.items():
        if varname not in input_dict:
            continue

        valstr = input_dict[varname]
        if valstr == "":
            continue

        # TODO: this might make us vulnerable to injection code
        try:
            inputs[varname] = vartype(valstr)
        except ValueError:
            print(f"Error converting value {varname}={valstr} to {vartype}")
    return inputs


def run_model(
    scenario_inputs: list[dict[str, Any]], request: HttpRequest
) -> list[dict[str, NDArray[Any]]]:
    """
    Run the model for the inputs
    @param scenario_inputs
    @param request
    @returns Climate model run outputs
    """

    # Get cambio inputs from GET params for saving to cookies
    # and if the new scenario is different from all old scenarios, add it
    inputs = parse_cambio_inputs_for_cookies(request.GET)
    new_hash = str(hash(json.dumps(inputs)))
    if new_hash not in request.COOKIES.keys():
        scenario_inputs.append(inputs)

    # Run the model
    scenarios: list[dict[str, NDArray[Any]]] = []
    for scenario_input in scenario_inputs:
        climate, _ = cambio(
            scenario_input["start_year"],
            scenario_input["stop_year"],
            scenario_input["dtime"],
            scenario_input["inv_time_constant"],
            scenario_input["transition_year"],
            scenario_input["transition_duration"],
            scenario_input["long_term_emissions"],
            scenario_input["stochastic_c_atm_std_dev"],
            scenario_input["albedo_with_no_constraint"],
            scenario_input["albedo_feedback"],
            scenario_input["stochastic_C_atm"],
            scenario_input["temp_anomaly_feedback"],
        )
        scenarios.append(climate)
    return scenarios


def make_plots(
    scenarios: list[dict[str, NDArray[Any]]],
    scenario_units: dict[str, str],
    carbon_vars: list[str],
    flux_vars: list[str],
    temp_vars: list[str],
) -> tuple[list[Any], list[str]]:
    """
    Return the plots that will be displayed
    @param scenarios  The climate model run results
    @param scenario_units The climate model run inputs (only units currently used)
    @returns  The plots
    """

    if len(carbon_vars) <= 0:
        carbon_vars = ["C_atm"]
    if len(flux_vars) <= 0:
        flux_vars = ["F_ha"]
    if len(temp_vars) <= 0:
        temp_vars = ["T_C"]

    climvarval_selected_names = [carbon_vars, flux_vars, temp_vars, ["pH"], ["albedo"]]
    climvarval_labels = ["Carbon amount", "Flux", "Temperature", "pH", "albedo"]
    units = [
        scenario_units["carbon_units"],
        scenario_units["flux_units"],
        scenario_units["temp_units"],
        "",
        "",
    ]

    # Loop over variables and create the plots
    plot_divs: list[Any] = []
    for list_of_names, ylabel in zip(climvarval_selected_names, climvarval_labels):
        names: list[str] = []
        years: list[NDArray[Any]] = []
        climvarvals: list[float | NDArray[Any]] = []
        for i, name in enumerate(list_of_names):
            unit_name = ""
            label = name
            if name == "T_C":  # or name == "T_anomaly":
                unit_name = scenario_units["temp_units"]
                label = "T" + " (" + unit_name + ")"
            else:
                label += ""

            for j, scenario in enumerate(scenarios):
                if unit_name == "F":
                    yvals = celsius_to_f(scenario[name])
                elif unit_name == "K":
                    yvals = celsius_to_kelvin(scenario[name])
                elif unit_name == "C":
                    yvals = scenario[name]
                else:
                    yvals = scenario[name]
                climvarvals.append(yvals)
                years.append(scenario["year"])
                names.append(f"Scenario {j}: {label}")

        plot_divs.append(
            plot(
                {
                    "data": [
                        Scatter(
                            x=xvals,
                            y=yvals,
                            mode="lines",
                            name=name,
                            opacity=0.8,
                            marker_color=getcolor(i),
                        )
                        for i, (xvals, yvals, name) in enumerate(
                            zip(years, climvarvals, names)
                        )
                    ],
                    "layout": {"xaxis": {"title": "year"}, "yaxis": {"title": ylabel}},
                },
                output_type="div",
                include_plotlyjs=False,
            )
        )

    return plot_divs, units


def index(request: HttpRequest) -> HttpResponse:
    """
    Create the view for the main page
    @param request  The HttpRequest
    """

    # Choices of what to plot
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

    # Get cambio inputs from cookies
    cookie_scenarios = [json.loads(value) for value in request.COOKIES.values()]
    cookie_scenarios = list(filter(lambda x: isinstance(x, dict), cookie_scenarios))
    scenario_inputs = [parse_cambio_inputs(scenario) for scenario in cookie_scenarios]
    scenario_units = get_scenario_units(request)
    carbon_vars = get_scenario_vars(request, carbon_vars_to_plot)
    flux_vars = get_scenario_vars(request, flux_vars_to_plot)
    temp_vars = get_scenario_vars(request, temp_vars_to_plot)

    # Run the model on old and new inputs to get the climate model results
    # (Packed into "scenarios")
    scenarios = run_model(scenario_inputs, request)

    # Make the plots
    plot_divs, _ = make_plots(
        scenarios,
        scenario_units,
        list(carbon_vars.keys()),
        list(flux_vars.keys()),
        list(temp_vars.keys()),
    )
    plot_div_stuff = [
        [var_to_plot, plot_div, unit]
        for var_to_plot, plot_div, unit in zip(vars_to_plot, plot_divs, units)
    ]

    # Variables to pass to html
    context = {
        "plot_divs": plot_div_stuff,
        "vars_to_plot": vars_to_plot,
    }
    response = render(request, "cambio/index.html", context)

    # save latest run in cookies
    scenario = json.dumps(scenario_inputs[-1])
    scenario_hash = str(hash(scenario))
    # don't add the new scenario to cookies if it already exists
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
