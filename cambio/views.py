"""
By Penny Rowe and Daniel Neshyba-Rowe
2022/12/21

Inspired by Benchly, by Ben Gamble, Charlie Dahl, and Penny Rowe
"""

import json

from typing import Any
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from cambio.utils.view_utils import run_model_for_dict

#    make_plots,
from cambio.utils.make_plots import MakePlots
from cambio.utils.schemas import CambioInputs, ScenarioInputs


def get_scenarios(request: HttpRequest, get_prefix: str) -> list[str]:
    """
    Get the scenario ids to plot
    @params request  The HttpRequest
    @returns The scenario ids to plot
    """
    scenario_ids: list[str] = []
    for get_param in request.GET.keys():
        if not get_param.startswith(get_prefix):
            continue
        scenario_ids.append(get_param[len(get_prefix) :])
    return scenario_ids


def include_default(scenario_inputs, default: str):
    """
    Always include default scenario in the list of scenarios
    @params scenario_inputs
    @params
    """
    if default not in scenario_inputs:
        dflt_params = {
            "inv_time_constant": [""],
            "transition_year": [""],
            "transition_duration": [""],
            "long_term_emissions": [""],
            "albedo_with_no_constraint": [""],
            "albedo_feedback": [""],
            "temp_anomaly_feedback": [""],
            "stochastic_C_atm": [""],
            "stochastic_c_atm_std_dev": [""],
            "scenario_name": ["hi"],
            "F_ha": ["on"],
            "flux": ["GtC/year"],
            "C_atm": ["on"],
            "carbon": ["GtC"],
            "T_anomaly": ["on"],
            "temp": ["C"],
            "pH": ["on"],
            "albedo": ["on"],
        }
        scenario_inputs[default] = CambioInputs.from_dict(dflt_params)


def index(request: HttpRequest) -> HttpResponse:
    """
    Create the view for the main page
    @param request  The HttpRequest
    """

    # TODO List
    # Add net fluxes to 1st figure (e.g., from point of view of to the atmosphere)
    # No need to run climate model for the default (but this may be moot)
    # Change the constrain albedo business so that if False, to make unconstrained = False or True
    # Maybe change "plot" to "update plot"?
    # Really need to align the x-axis so that times are always at the same position on the screen
    # It would be nice to be able to rename scenarios, and also have a way to add a notes elaborating on them
    # When curves are right on top of one another, it would be useful to have markers
    # Remove start/stop year and dtime from display for added scenarios
    # Improve variable names under Add new scenario

    # Get variables from request:
    scenarios_ids_to_plot = get_scenarios(request, "plot_scenario_")
    scenarios_ids_to_delete = get_scenarios(request, "del_scenario")

    # Get variables from request for use in plots
    inputs = request.GET

    # Name of default scenario
    default = "Default"

    # Get the scenario inputs:
    # - Always include the default first (it can be overridden)
    scenario_inputs: dict[str, CambioInputs] = {}
    include_default(scenario_inputs, default)
    # - Then add old scenarios from cookies
    for scenario_id, scenario in request.COOKIES.items():
        scenario_inputs[scenario_id] = CambioInputs.from_json(scenario)
    # - Finally, get new scenario from get parameters only if it exists
    new_scenario_id = request.GET.get("scenario_name", "")
    if new_scenario_id != "":
        scenario_inputs[new_scenario_id] = CambioInputs.from_dict(request.GET)

    # Remove scenarios that are scheduled to be deleted
    # - Never remove the default
    if default in scenarios_ids_to_delete:
        scenarios_ids_to_delete.remove(default)
    # - Remove the other scenarios
    scenario_inputs = {
        key: value
        for key, value in scenario_inputs.items()
        if key not in scenarios_ids_to_delete
    }

    # Run the model on old and new inputs to get the climate model results
    # (Packed into "scenarios")
    scenarios = run_model_for_dict(scenario_inputs)
    scenarios_ids_to_plot = [sid for sid in scenarios_ids_to_plot if sid in scenarios]

    # If nothing else is indicated for plotting, plot the default
    if len(scenarios_ids_to_plot) == 0:
        scenarios_ids_to_plot = [default]

    scenarios_to_plot = [scenarios[sid] for sid in scenarios_ids_to_plot]

    # Create the plots (for passing to the html)
    makePlots = MakePlots(inputs)
    plot_divs = makePlots.make(scenarios_to_plot)

    # Get the other variables to pass to the html
    scenario_ids = list(scenarios.keys())
    old_scenario_inputs = {sid: inp.dict() for sid, inp in scenario_inputs.items()}
    plot_scenario_choices = [[sid, f"plot_scenario_{sid}"] for sid in scenario_ids]
    plot_scenario_ids = [sid for sid in scenarios_ids_to_plot if sid in scenarios]

    # Variables to pass to html
    context = {
        "plot_divs": plot_divs,
        "old_scenario_inputs": old_scenario_inputs,
        "plot_scenario_choices": plot_scenario_choices,
        "plot_scenario_ids": plot_scenario_ids,
        "inputs": ScenarioInputs().dict(),
    }
    response = render(request, "cambio/index.html", context)

    # If there is a new scenario in the get parameters, save it to cookies
    if new_scenario_id != "":
        scenario = scenario_inputs[new_scenario_id].json()
        response.set_cookie(new_scenario_id, scenario)

    # delete all unwanted scenarios:
    for cookie_name in scenarios_ids_to_delete:
        response.delete_cookie(cookie_name)

    return response
