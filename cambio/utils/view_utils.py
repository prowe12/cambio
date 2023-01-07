"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

Based on Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

from typing import Any
from plotly.offline import plot
from plotly.graph_objs import Scatter
from django.http import QueryDict
from numpy.typing import NDArray

from cambio.utils.cambio import cambio
from cambio.utils.scenarios import CambioInputs
from cambio.utils.cambio_utils import CambioVar, celsius_to_f, celsius_to_kelvin


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
# ) -> dict[dict[str, CambioVar]]:
def run_model_for_dict(
    scenario_inputs: dict[str, CambioInputs]
) -> dict[str, dict[str, CambioVar]]:
    """
    Run the model for the inputs
    @param scenario_inputs
    @param request
    @returns Climate model run outputs
    """
    # Run the model
    # scenarios: dict[dict[str, CambioVar]] = {}
    scenarios: dict[str, dict[str, CambioVar]] = {}
    for scenario_id, scenario_input in scenario_inputs.items():
        climate, _ = cambio(scenario_input)
        scenarios[scenario_id] = climate
    return scenarios


def return_same(x: float) -> float:
    return x


def dt_c_to_dt_f(x: float) -> float:
    return x * 9 / 5


def gtc_to_gtco2(x: float) -> float:
    return x / 0.27


def gtc_to_atm(x: float) -> float:
    return x / 2.12


# class MakePlots:
#     """
#     Make the plots, depending on user-specified variables and units.
#     Use defaults when not specified
#     """

#     def __init__(self):
#         self.carbon_vars_to_plot = ["C_atm", "C_ocean"]
#         self.flux_vars_to_plot = ["F_ha", "F_ao", "F_oa", "F_la", "F_al"]
#         self.temp_vars_to_plot = ["T_anomaly", "T_C"]
#         self.vars_to_plot = [
#             carbon_vars_to_plot,
#             flux_vars_to_plot,
#             temp_vars_to_plot,
#             [],
#             [],
#         ]  # , ['pH'], ['albedo']]


def make_plots(
    scenarios: list[dict[str, CambioVar]],
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
        scenario_units["carbon"],
        scenario_units["flux"],
        scenario_units["temp"],
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
        years: list[CambioVar] = []
        climvarvals: list[float | CambioVar] = []
        for name in list_of_names:
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
