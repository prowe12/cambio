"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

Based on Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

import json

from typing import Any
from plotly.offline import plot
from plotly.graph_objs import Scatter
from django.http import QueryDict
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


def parse_inputs(
    input_dict: dict[str, Any] | QueryDict,
    default_inputs: dict[str, int | float | bool | str],
    input_types: dict[str, Any],
) -> dict[str, Any]:
    """
    Parse the inputs
    @param input_dict  A hashmap of the input variable names and their values as strings
    @param inputs  The variables to get
    @params varnames The types of the variables
    @returns  A hashmap of the input variable names and their values as the proper type
    """
    parsed_inputs: dict[str, Any] = {}
    for varname, vartype in input_types.items():

        # set values default initially
        parsed_inputs[varname] = default_inputs[varname]

        # if not specified, keep them at default
        if varname not in input_dict:
            continue
        valstr = input_dict[varname]
        if valstr == "":
            continue

        # if specified, set to specified
        # TODO: this might make us vulnerable to injection code
        try:
            parsed_inputs[varname] = vartype(valstr)
        except ValueError:
            print(f"Error converting value {varname}={valstr} to {vartype}")
    return parsed_inputs


# def run_model_for_dict(
#     scenario_inputs: dict[dict[str, Any]]
# ) -> dict[dict[str, NDArray[Any]]]:
def run_model_for_dict(scenario_inputs):
    """
    Run the model for the inputs
    @param scenario_inputs
    @param request
    @returns Climate model run outputs
    """
    # Run the model
    # scenarios: dict[dict[str, NDArray[Any]]] = {}
    scenarios = {}
    for scenario_id, scenario_input in scenario_inputs.items():
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
        scenarios[scenario_id] = climate
    return scenarios


def return_same(x):
    return x


def dt_c_to_dt_f(x):
    return x * 9 / 5


def gtc_to_gtco2(x):
    return x / 0.27


def gtc_to_atm(x):
    return x / 2.12


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
    if len(scenarios) == 0:
        return plot_divs, units

    for list_of_names, ylabel, unit in zip(
        climvarval_selected_names, climvarval_labels, units
    ):
        names: list[str] = []
        years: list[NDArray[Any]] = []
        climvarvals: list[float | NDArray[Any]] = []
        for i, name in enumerate(list_of_names):
            unit_name = unit
            label = name
            conversion_fun = return_same
            if name in ("C_atm", "C_ocean"):
                if unit_name == "atm":
                    conversion_fun = gtc_to_atm
                elif unit_name == "GtCO2":
                    conversion_fun = gtc_to_gtco2

            elif name == "T_C":
                if unit_name == "F":
                    conversion_fun = celsius_to_f
                elif unit_name == "K":
                    conversion_fun = celsius_to_kelvin
            elif name == "T_anomaly":
                if unit_name == "F":
                    conversion_fun = dt_c_to_dt_f
                else:
                    yvals = scenario[name]
            elif name in ("F_ha", "F_la", "F_al", "F_ao", "F_oa"):
                if unit_name == "GtCO2/year":
                    conversion_fun = gtc_to_gtco2

            for j, scenario in enumerate(scenarios):
                yvals = conversion_fun(scenario[name])

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


# def run_model(
#     scenario_inputs: list[dict[str, Any]], request: HttpRequest
# ) -> list[dict[str, NDArray[Any]]]:
#     """
#     Run the model for the inputs
#     @param scenario_inputs
#     @param request
#     @returns Climate model run outputs
#     """

#     # Get cambio inputs from GET params for saving to cookies
#     # and if the new scenario is different from all old scenarios, add it
#     inputs = parse_cambio_inputs_for_cookies(request.GET)
#     new_hash = str(hash(json.dumps(inputs)))
#     if new_hash not in request.COOKIES.keys():
#         scenario_inputs.append(inputs)

#     # Run the model
#     scenarios: list[dict[str, NDArray[Any]]] = []
#     for scenario_input in scenario_inputs:
#         climate, _ = cambio(
#             scenario_input["start_year"],
#             scenario_input["stop_year"],
#             scenario_input["dtime"],
#             scenario_input["inv_time_constant"],
#             scenario_input["transition_year"],
#             scenario_input["transition_duration"],
#             scenario_input["long_term_emissions"],
#             scenario_input["stochastic_c_atm_std_dev"],
#             scenario_input["albedo_with_no_constraint"],
#             scenario_input["albedo_feedback"],
#             scenario_input["stochastic_C_atm"],
#             scenario_input["temp_anomaly_feedback"],
#         )
#         scenarios.append(climate)
#     return scenarios


# def parse_cambio_inputs(input_dict: dict[str, Any]) -> dict[str, Any]:
#     """
#     Parse the inputs
#     @param input_dict  A hashmap of the input variable names and their values as strings
#     @returns  A hashmap of the input variable names and their values as the proper type
#     """

#     # Default values
#     inputs = {
#         "start_year": 1750.0,  # <!-- start_year"><br> -->
#         "stop_year": 2200.0,  # stop_year"><br> -->
#         "dtime": 1.0,  # dtime"><br> time resolution (years) -->
#         "inv_time_constant": 0.025,  # inv_time_constant"><br> -->
#         "transition_year": 2040.0,  # transition_year"><br> # year to start decreasing CO2 -->
#         "transition_duration": 20.0,  # transition_duration"><br> years over which to decrease co2  -->
#         "long_term_emissions": 2.0,  # long_term_emissions"><br> # ongoing carbon emissions after decarbonization  -->
#         "albedo_with_no_constraint": False,  # albedo_with_no_constraint"><br> -->
#         "albedo_feedback": False,  # albedo_feedback"><br> -->
#         "temp_anomaly_feedback": False,  # temp_anomaly_feedback"><br> -->
#         "stochastic_C_atm": False,  # stochastic_C_atm"><br> -->
#         "stochastic_c_atm_std_dev": 0.1,  # stochastic_c_atm_std_dev"> <br> -->
#         "temp_units": "F",  # temp_units"><br> # F, C, or K -->
#         "c_units": "GtC",  # c_units"><br> GtC, GtCO2, atm  -->
#         "flux_type": "/year",  # flux_type"><br> # total, per year-->
#         "plot_flux_diffs": True,  # plot_flux_diffs"><br> -->
#     }
#     varnames = {
#         "start_year": float,
#         "stop_year": float,
#         "dtime": float,
#         "inv_time_constant": float,
#         "transition_year": float,
#         "transition_duration": float,
#         "long_term_emissions": float,
#         "albedo_with_no_constraint": bool,
#         "albedo_feedback": bool,
#         "temp_anomaly_feedback": bool,
#         "stochastic_C_atm": bool,
#         "stochastic_c_atm_std_dev": float,
#         "temp_units": str,
#         "c_units": str,
#         "flux_type": str,
#         "plot_flux_diffs": bool,
#     }

#     for varname, vartype in varnames.items():
#         if varname not in input_dict:
#             continue

#         valstr = input_dict[varname]
#         if valstr == "":
#             continue

#         # TODO: this might make us vulnerable to injection code
#         try:
#             inputs[varname] = vartype(valstr)
#         except ValueError:
#             print(f"Error converting value {varname}={valstr} to {vartype}")
#     return inputs

# def parse_cambio_inputs_for_units(input_dict: QueryDict) -> dict[str, Any]:
#     """
#     Parse the inputs
#     @param input_dict  A hashmap of the input variable names and their values as strings
#     @returns  A hashmap of the input variable names and their values as the proper type
#     """

#     # Default values
#     inputs = {
#         "temp_units": "F",  # temp_units"><br> # F, C, or K -->
#         "carbon_units": "GtC",  # c_units"><br> GtC, GtCO2, atm  -->
#         "flux_units": "GtC/year",  # flux_type"><br> # total, per year-->
#     }
#     varnames = {
#         "temp_units": str,
#         "carbon_units": str,
#         "flux_units": str,
#     }

#     for varname, vartype in varnames.items():
#         if varname not in input_dict:
#             continue

#         valstr = input_dict[varname]
#         if valstr == "":
#             continue

#         # TODO: this might make us vulnerable to injection code
#         try:
#             inputs[varname] = vartype(valstr)
#         except ValueError:
#             print(f"Error converting value {varname}={valstr} to {vartype}")
#     return inputs
